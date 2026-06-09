"""ghost.reviews dashboard — the demo face.

Paste a product (Amazon listing, etc.) → we pull its reviews from the live web,
run the adversarial teardown (one AI that knows how the model families write +
compares each review to its own self-written baselines), flag which are AI
ghostwritten, show how the AI is steering the rating, and give a trust verdict.

Run:  streamlit run app.py
"""

import os

import streamlit as st
from dotenv import load_dotenv

from ghost.nimble_client import using_samples
from ghost.pipeline import run

load_dotenv()

# On Streamlit Community Cloud secrets live in st.secrets, not the environment,
# but the pipeline reads keys via os.getenv. Bridge them so the SAME code runs
# live on Cloud (key in Secrets) and locally (key in .env) with no branching.
for _k in ("NIMBLE_API_KEY", "ANTHROPIC_API_KEY"):
    try:
        if not os.getenv(_k) and _k in st.secrets:
            os.environ[_k] = str(st.secrets[_k])
    except Exception:
        pass  # no secrets.toml at all (pure local) — env/.env already covers it

st.set_page_config(page_title="ghost.reviews", page_icon="👻", layout="centered")

st.title("👻 ghost.reviews")
st.caption("Which reviews are real humans — and which are AI ghostwriters steering you?")

# Be explicit about where the data is coming from so judges aren't misled.
if using_samples():
    st.caption("🔧 **Sample mode:** a built-in representative dataset (reviews *with* star "
               "ratings) so you can see the full human-vs-AI **rating-gap** verdict. "
               "Add `NIMBLE_API_KEY` to pull **live web reviews** via Nimble instead.")
else:
    st.caption("🟢 **Live mode:** reviews pulled from the live web via Nimble. "
               "Verdict rests on the per-review human-vs-AI teardown; the rating-gap "
               "metric fills in only when the source exposes per-review stars.")

product = st.text_input("Product (name or listing URL)",
                        placeholder="e.g. Bose QuietComfort Ultra earbuds")
max_results = st.slider("How many reviews to scan", 5, 25, 8)

if st.button("Scan for ghosts", type="primary", disabled=not product):
    with st.spinner("Pulling reviews and tearing them apart…"):
        try:
            result = run(product, max_results=max_results)
        except Exception as e:
            st.error(f"Couldn't fetch/score reviews: {e}")
            st.stop()
    s = result["summary"]

    if s.get("total", 0) == 0:
        st.warning("No reviews found for that product. Try a different name or listing URL.")
        st.stop()

    # --- the trust verdict (the payoff) ---
    if s["trust"].startswith("AVOID"):
        st.error(f"🚫 {s['trust']}")
    elif s["trust"].startswith("LOOKS GENUINE"):
        st.success(f"✅ {s['trust']}")
    else:
        st.warning(f"⚠️ {s['trust']}")

    def stars(val):
        return f"{val} ★" if val is not None else "—"

    c1, c2, c3 = st.columns(3)
    c1.metric("AI-written", f"{s['pct_ai']}%", f"{s['ai_count']} of {s['total']}")
    c2.metric("Listed rating", stars(s["overall_rating"]))
    delta = None
    if s["human_rating"] is not None and s["overall_rating"] is not None:
        delta = round(s["human_rating"] - s["overall_rating"], 1)
    c3.metric("Real human rating", stars(s["human_rating"]), delta)

    if s.get("suspect_count"):
        st.caption(f"({s['suspect_count']} borderline 'suspect' reviews excluded "
                   "from the human rating.)")

    if s["direction"] == "inflating":
        st.write("📈 **The AI reviews are inflating the rating** — the score is propped up.")
    elif s["direction"] == "bombing":
        st.write("📉 **The AI reviews are attacking the product** — humans rate it higher.")

    # --- the self-written reference reviews (the "mirror") ---
    with st.expander("🪞 What our AI wrote to compare against"):
        st.caption("Our analyzer writes its own reviews — one a human would write, "
                   "one an AI would — then compares every real review to these.")
        st.markdown(f"**Genuine-human baseline:** {result['baselines']['human']}")
        st.markdown(f"**AI-ghostwriter baseline:** {result['baselines']['ai']}")

    # --- family attribution preview (roadmap) ---
    tally = s.get("family_preview_tally") or {}
    if tally:
        chips = " · ".join(f"{k} ×{v}" for k, v in tally.items())
        st.info(f"🧪 **[ROADMAP PREVIEW] Closest model family:** {chips}\n\n"
                "Family-level only, low-confidence estimates — **not an identification.** "
                "As we build a dataset of real AI-vs-human reviews this will sharpen. "
                "Shown as a direction for future validation, never a claim.")

    st.divider()
    st.subheader("Reviews — most AI-like first")

    for r in sorted(result["reviews"], key=lambda x: -x["ai_likelihood"]):
        score = r["ai_likelihood"]
        icon = "👻" if score >= 60 else ("⚠️" if score >= 40 else "🧑")
        rstars = "★" * int(r.get("rating") or 0) if r.get("rating") else ""
        label = f"{icon}  {score}% AI · {rstars}  {r['title'] or r['url'] or 'review'}"
        with st.expander(label):
            st.write(r["text"])
            st.caption("Teardown: " + ", ".join(r["reasons"]))
            leans = r.get("leans") or {}
            if leans:
                st.caption(f"Similarity — AI baseline {leans.get('ai', 0):.0%} · "
                           f"human baseline {leans.get('human', 0):.0%}")
            fp = r.get("family_preview")
            if fp:
                st.caption(f"🧪 Closest family (PREVIEW — not an identification, "
                           f"~{fp['confidence']}% confidence as a direction): {fp['family']}")
            if r.get("url"):
                st.caption(f"Source: {r['url']}")
