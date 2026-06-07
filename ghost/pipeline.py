"""Tower entry point — the deployed data pipeline for ghost.reviews.

Run order:  Nimble (live reviews)  ->  Claude (score each)  ->  store results.

On Tower:   tower run --parameter=product="Acme Wireless Earbuds"
Locally:    GHOST_PRODUCT="Acme Wireless Earbuds" python -m ghost.pipeline

Secrets (NIMBLE_API_KEY, ANTHROPIC_API_KEY) are read via os.getenv — set them
locally in .env, or on Tower with `tower secrets create`.
"""

import json
import os

from ghost.detector import analyze, score_reviews, self_baselines
from ghost.lakehouse import write_scan
from ghost.nimble_client import fetch_reviews


def run(product: str, max_results: int = 10) -> dict:
    reviews = fetch_reviews(product, max_results=max_results)
    scored = score_reviews(reviews, product=product)
    summary = analyze(scored)
    return {
        "product": product,
        "summary": summary,
        "baselines": self_baselines(product),
        "reviews": scored,
    }


def main():
    # Tower passes parameters as env vars; fall back to a local env var.
    product = os.getenv("product") or os.getenv("GHOST_PRODUCT")
    if not product:
        raise SystemExit(
            "No product given. Tower: --parameter=product='...'  "
            "Local: GHOST_PRODUCT='...'"
        )
    max_results = int(os.getenv("max_results", "10"))

    result = run(product, max_results=max_results)

    # Persist results. Locally -> JSON file. On Tower you can swap this for an
    # Iceberg write to the lakehouse (see README — pyiceberg snippet) so the
    # Tower judges see data landing in storage.
    out_path = os.getenv("GHOST_OUTPUT", "ghost_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Land the summary in the Tower lakehouse (no-ops locally without a catalog).
    print(write_scan(result))

    s = result["summary"]
    print(f"\nghost.reviews — {product!r}")
    print(f"  {s['pct_ai']}% of reviews look AI-written "
          f"({s['ai_count']} AI / {s['human_count']} human of {s['total']})")
    print(f"  Listed rating: {s['overall_rating']}  |  "
          f"Real human rating: {s['human_rating']}  |  AI rating: {s['ai_rating']}")
    print(f"  AI is {s['direction']} the score.  Verdict: {s['trust']}")
    print(f"  Full results -> {out_path}")


if __name__ == "__main__":
    main()
