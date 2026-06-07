"""The brain of ghost.reviews — ONE analyzing AI (no other live models).

For each review it runs an ADVERSARIAL TEARDOWN:
  1. It knows how each model family tends to write (ghost/model_profiles.py).
  2. It writes its OWN reference reviews of the product — one a genuine human
     would write, one an AI ghostwriter would write — and compares the suspect
     review against both.
  3. It scores how likely the review is AI-ghostwritten (vs human) + the red
     flags, and names the CLOSEST model family as a clearly-labeled PREVIEW.

Then the payoff: across all reviews, how much of the rating is propped up (or
attacked) by AI, the real-human rating, and a trust verdict.

Two modes, same interface:
  • Default: fast, free, no-API rule engine (works offline, $0).
  • Optional: set ANTHROPIC_API_KEY to upgrade the teardown to Claude.
"""

import os
import re

from ghost.model_profiles import MODEL_FAMILIES, families_brief

# ---- AI-writing red flags (rule-based, free) ------------------------------

HYPE_WORDS = [
    "best", "amazing", "incredible", "perfect", "flawless", "must buy",
    "must-buy", "highly recommend", "the best", "love it", "wow", "fantastic",
    "absolutely", "life changing", "life-changing",
]
FREEBIE_FLAGS = [
    "received", "free in exchange", "in exchange for", "for review",
    "review club", "discounted", "complimentary", "sponsored",
]
HUMAN_SIGNALS = [
    "but", "however", "after", "weeks", "months", "days", "battery", "returned",
    "support", "disconnect", "creak", "weak", "mediocre", "flaky", "cheap",
    "stopped", "issue", "problem", "though", "honestly", "pocket", "laptop",
]

_STOP = set("the a an and or of to is it for in on with this that i my you we "
            "they are was were be been so very really just too as at by".split())


# ---- self-written reference reviews (the "writes its own to compare" step) -

def self_baselines(product: str) -> dict:
    """The analyzer writes its OWN reviews of the product to compare against:
    one a real human would write, one an AI ghostwriter would write."""
    return {
        "human": (
            f"Used the {product} for a few weeks now. It's decent — does the job, "
            f"but the build feels a bit cheap and it had a minor issue on day three "
            f"that I worked around. For the price I'd buy it again, with caveats."
        ),
        "ai": (
            f"The {product} is absolutely amazing! Best product ever, perfect in "
            f"every way. Incredible quality, highly recommend to everyone. Five "
            f"stars, you will love it, a must buy!"
        ),
    }


def _tokens(text: str) -> set:
    return {w for w in re.findall(r"[a-z']+", text.lower()) if w not in _STOP and len(w) > 2}


def _similarity(a: str, b: str) -> float:
    """Jaccard token overlap, 0..1 — cheap, free, good enough to lean a verdict."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


# ---- closest model family (PREVIEW — never a certainty) -------------------

def closest_family(text: str) -> dict | None:
    """Rough cue-matching against each family's writing tendencies.

    Returns {"family", "confidence", "preview": True} or None when there isn't
    enough signal. Family-level only, always low-confidence by design — this is
    the roadmap preview, not a claim.
    """
    t = text.lower()
    scores = {}
    for name, info in MODEL_FAMILIES.items():
        hits = sum(1 for c in info.get("cues", []) if c in t)
        if hits:
            scores[name] = hits
    if not scores:
        return None
    best = max(scores, key=scores.get)
    total = sum(scores.values())
    # Confidence is deliberately capped low — we never claim certainty.
    confidence = min(60, round(100 * scores[best] / total) // 2 + 25)
    return {"family": best, "confidence": confidence, "preview": True}


# ---- per-review teardown (rule engine) ------------------------------------

def _teardown_one(text: str, baselines: dict) -> dict:
    """Adversarial teardown of a single review → score + reasons + family + leans."""
    t = text.lower()
    score = 30
    reasons: list[str] = []

    hype = sum(t.count(w) for w in HYPE_WORDS)
    if hype >= 3:
        score += 35
        reasons.append(f"{hype} generic hype phrases")
    elif hype == 2:
        score += 20
        reasons.append("stacked generic superlatives")

    if any(f in t for f in FREEBIE_FLAGS):
        score += 25
        reasons.append("incentivized / free-product disclosure")

    specifics = sum(1 for s in HUMAN_SIGNALS if s in t)
    if specifics >= 3:
        score -= 40
        reasons.append("concrete, specific details (reads human)")
    elif specifics == 0:
        score += 15
        reasons.append("no concrete usage details")

    words = re.findall(r"[a-z]+", t)
    if words:
        top = max(set(words), key=words.count)
        if words.count(top) >= 4 and len(top) > 3:
            score += 20
            reasons.append(f"repeated word '{top}' x{words.count(top)}")

    if text.count("!") >= 3:
        score += 10
        reasons.append("exclamation-mark spam")

    # Compare against the analyzer's OWN reference reviews.
    sim_ai = _similarity(text, baselines["ai"])
    sim_human = _similarity(text, baselines["human"])
    if sim_ai > sim_human:
        score += 12
        reasons.append(f"reads closer to the AI baseline ({sim_ai:.0%} vs {sim_human:.0%})")
    elif sim_human > sim_ai:
        score -= 12
        reasons.append(f"reads closer to the human baseline ({sim_human:.0%} vs {sim_ai:.0%})")

    score = max(0, min(100, score))
    if score >= 60:
        verdict = "likely_ai"
    elif score >= 40:
        verdict = "suspect"
    else:
        verdict = "human"
    if not reasons:
        reasons = ["no strong signals either way"]

    family = closest_family(text) if score >= 60 else None
    return {
        "ai_likelihood": score,
        "verdict": verdict,
        "reasons": reasons,
        "leans": {"ai": round(sim_ai, 2), "human": round(sim_human, 2)},
        "family_preview": family,
    }


def score_reviews(reviews: list[dict], product: str = "this product") -> list[dict]:
    """Run the teardown on every review.

    Uses Claude if ANTHROPIC_API_KEY is set, else the free rule engine.
    """
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            return _score_with_claude(reviews, product)
        except Exception as e:  # never let the demo die
            print(f"[detector] Claude teardown failed ({e}); using rule engine.")

    baselines = self_baselines(product)
    out = []
    for r in reviews:
        out.append({**r, **_teardown_one(r.get("text", ""), baselines)})
    return out


def analyze(scored: list[dict]) -> dict:
    """The payoff: human-vs-AI breakdown, the rating gap, and a trust verdict."""
    if not scored:
        return {"verdict": "no_data", "total": 0,
                "trust": "NO DATA — no reviews found", "pct_ai": 0,
                "ai_count": 0, "human_count": 0, "suspect_count": 0,
                "overall_rating": None, "human_rating": None, "ai_rating": None,
                "direction": "none", "family_preview_tally": {}}

    n = len(scored)
    ai = [r for r in scored if r["ai_likelihood"] >= 60]
    suspect = [r for r in scored if 40 <= r["ai_likelihood"] < 60]
    # Only CONFIDENT human reviews (< 40) anchor the "real human rating" — folding
    # in suspect reviews would inflate it and weaken the trust signal.
    human = [r for r in scored if r["ai_likelihood"] < 40]
    pct_ai = round(100 * len(ai) / n)

    def avg_rating(rows):
        rated = [r["rating"] for r in rows if r.get("rating") is not None]
        return round(sum(rated) / len(rated), 1) if rated else None

    overall_rating = avg_rating(scored)
    human_rating = avg_rating(human)
    ai_rating = avg_rating(ai)

    # Which way is the AI steering the score?
    direction = "none"
    if ai and human_rating is not None and ai_rating is not None:
        if ai_rating > human_rating + 0.4:
            direction = "inflating"      # astroturfing the rating UP
        elif ai_rating < human_rating - 0.4:
            direction = "bombing"        # review-bombing it DOWN

    # Trust call.
    if pct_ai >= 50 and direction == "inflating":
        trust = "AVOID — rating is propped up by AI"
    elif pct_ai >= 50 and direction == "bombing":
        trust = "INVESTIGATE — humans like it, AI is attacking it"
    elif pct_ai >= 25:
        trust = "BE CAREFUL — meaningful AI review activity"
    else:
        trust = "LOOKS GENUINE — mostly real human reviews"

    # Tally the family preview (clearly a preview — never asserted).
    families: dict[str, int] = {}
    for r in ai:
        fp = r.get("family_preview")
        if fp:
            families[fp["family"]] = families.get(fp["family"], 0) + 1

    return {
        "total": n,
        "ai_count": len(ai),
        "human_count": len(human),
        "suspect_count": len(suspect),
        "pct_ai": pct_ai,
        "overall_rating": overall_rating,
        "human_rating": human_rating,
        "ai_rating": ai_rating,
        "direction": direction,
        "trust": trust,
        "family_preview_tally": families,
    }


# ---- optional Claude upgrade ----------------------------------------------

def _parse_scores(raw: str) -> dict:
    """Extract + validate the scores JSON from a model response.

    Tolerant of preamble text and ```json fences. Raises ValueError on a wrong
    shape so the caller falls back to the rule engine — never silently returns
    an empty result (which would mark every review 'human').
    """
    import json
    import re

    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    else:
        # Grab the outermost {...} if there's surrounding prose.
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]

    data = json.loads(text)  # may raise JSONDecodeError -> caught upstream
    scores = data.get("scores") if isinstance(data, dict) else None
    if not isinstance(scores, list) or not scores:
        raise ValueError("Claude response missing a non-empty 'scores' list")
    return data


def _score_with_claude(reviews: list[dict], product: str) -> list[dict]:
    import json
    from anthropic import Anthropic

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    baselines = self_baselines(product)
    numbered = [{"id": i, "text": r.get("text", "")} for i, r in enumerate(reviews)]

    system = (
        "You are a single forensic analyst that KNOWS how the major model "
        "families tend to write. Use this knowledge to tear each product review "
        "apart and judge whether a real human or an AI ghostwriter wrote it.\n\n"
        "How the families tend to write:\n" + families_brief() + "\n\n"
        "Rules: 'closest_family' is a low-confidence PREVIEW, family-level only "
        "(e.g. 'Gemini', never a version). Never claim certainty. Return ONLY JSON."
    )
    user = (
        "Reference reviews you wrote yourself for comparison:\n"
        f"  GENUINE-human style: {baselines['human']}\n"
        f"  AI-ghostwriter style: {baselines['ai']}\n\n"
        'Return {"scores":[{"id":int,"ai_likelihood":0-100,'
        '"verdict":"human"|"suspect"|"likely_ai","reasons":[str],'
        '"closest_family":str|null,"family_confidence":0-100}]}\n\n'
        "Reviews:\n" + json.dumps(numbered)
    )
    msg = client.messages.create(
        model=os.getenv("GHOST_MODEL", "claude-haiku-4-5-20251001"),
        max_tokens=3000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    data = _parse_scores(msg.content[0].text)
    by_id = {s["id"]: s for s in data["scores"]}

    out = []
    for i, r in enumerate(reviews):
        s = by_id.get(i, {})
        fam = s.get("closest_family")
        family_preview = (
            {"family": fam, "confidence": s.get("family_confidence", 40),
             "preview": True}
            if fam and s.get("ai_likelihood", 0) >= 60 else None
        )
        out.append({
            **r,
            "ai_likelihood": s.get("ai_likelihood", 50),
            "verdict": s.get("verdict", "suspect"),
            "reasons": s.get("reasons", ["no analysis"]),
            "leans": {"ai": _similarity(r["text"], baselines["ai"]),
                      "human": _similarity(r["text"], baselines["human"])},
            "family_preview": family_preview,
        })
    return out
