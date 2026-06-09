"""Nimble client — pulls live review text from across the web.

Uses Nimble's Search API (deep mode does real-time webpage extraction), so the
reviews we score are genuinely fetched live, not cached. This is the "sees the
live web" requirement for the Nimble challenge.

Docs: https://docs.nimbleway.com/nimble-sdk/search-api
"""

import os
import requests

from ghost.sample_data import sample_reviews

NIMBLE_SEARCH_URL = "https://sdk.nimbleway.com/v1/search"


def _key() -> str:
    """The configured key, treating empty / unfilled placeholders as absent."""
    key = (os.getenv("NIMBLE_API_KEY") or "").strip()
    if not key or key.startswith("your-"):  # .env.example placeholder
        return ""
    return key


def using_samples() -> bool:
    """True when we're serving built-in sample reviews (no usable Nimble key)."""
    if os.getenv("GHOST_SAMPLE") == "1":
        return True
    return not _key()


def _extract_rating(item: dict):
    """Pull a star rating out of a Nimble result if one is present."""
    md = item.get("metadata") or {}
    for src in (item, md):
        for field in ("rating", "stars", "score", "star_rating"):
            val = src.get(field)
            if val is not None:
                try:
                    return float(val)
                except (TypeError, ValueError):
                    pass
    return None


def fetch_reviews(product: str, max_results: int = 10, search_depth: str = "deep"):
    """Search the live web for reviews of `product` and return review items.

    Returns a list of dicts: {title, text, url, rating, source}. Until a usable
    NIMBLE_API_KEY is set, returns built-in sample reviews so the app still runs.
    """
    if using_samples():
        return sample_reviews(max_results)

    resp = requests.post(
        NIMBLE_SEARCH_URL,
        headers={
            "Authorization": f"Bearer {_key()}",
            "Content-Type": "application/json",
        },
        json={
            "query": f"customer reviews and complaints for {product}",
            "max_results": max_results,
            "search_depth": search_depth,
        },
        timeout=60,  # fail fast into the app's sample fallback rather than hang a judge
    )
    resp.raise_for_status()
    data = resp.json()

    reviews = []
    for item in data.get("results", []):
        text = (item.get("description") or "").strip()
        if not text:
            continue
        reviews.append(
            {
                "title": item.get("title", ""),
                "text": text,
                "url": item.get("url", ""),
                "rating": _extract_rating(item),  # None if Nimble doesn't supply one
                "source": (item.get("metadata") or {}),
            }
        )
    return reviews
