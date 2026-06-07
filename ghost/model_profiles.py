"""Knowledge base: how each major model family tends to write.

This is what makes our analyzing AI 'know how the other models function'. It is
NOT a fingerprint and NOT a certainty — these are documented behavioral
tendencies the analyzer reasons WITH when it tears a review down. Used today to
sharpen human-vs-AI detection, and to power the 'closest family (preview)'
roadmap feature.

Sourcing: these tendencies are hand-authored from publicly observable model
output (vendor style guides, published examples, and our own prompting). They
are intentionally coarse, illustrative starting points — NOT validated
fingerprints. The roadmap is to replace these heuristics with patterns learned
from a labeled dataset as it accumulates (the data flywheel). Until then,
family attribution is shipped as a low-confidence PREVIEW only.
"""

MODEL_FAMILIES = {
    "GPT / Copilot": {
        "tendencies": [
            "balanced, list-friendly structure",
            "hedged, polished, 'helpful assistant' tone",
            "frequent 'Overall,' / 'In summary,' wrap-ups",
            "neat parallel sentence structure",
        ],
        # Weak surface cues for the FREE rule matcher. Intentionally rough —
        # this is why family attribution is shipped as a PREVIEW, not a claim.
        "cues": [
            "overall", "in summary", "additionally", "furthermore",
            "it's worth noting", "pros", "cons", "in conclusion",
        ],
    },
    "Gemini": {
        "tendencies": [
            "upbeat, marketing-adjacent enthusiasm",
            "lots of adjectives stacked together",
            "tidy bullet-y phrasing, emoji-friendly",
            "tends to over-explain benefits",
        ],
        "cues": [
            "absolutely", "amazing", "perfect", "love", "stunning",
            "incredible", "elevate", "game-changer", "✨",
        ],
    },
    "Claude": {
        "tendencies": [
            "measured, qualifying language ('that said', 'to be fair')",
            "acknowledges trade-offs and nuance",
            "longer flowing sentences, fewer exclamations",
            "careful, slightly formal register",
        ],
        "cues": [
            "that said", "to be fair", "however", "nuance", "trade-off",
            "while", "although", "worth considering",
        ],
    },
    "DeepSeek": {
        "tendencies": [
            "direct, technical, spec-focused",
            "less idiomatic English, occasional stiffness",
            "fact-dense, lower emotional tone",
        ],
        "cues": [
            "specifications", "technical", "performance", "efficiency",
            "parameters", "in terms of", "from a", "perspective",
        ],
    },
    "Qwen": {
        "tendencies": [
            "concise, sometimes templated phrasing",
            "occasional translated-feeling constructions",
            "feature-listing without deep specifics",
        ],
        "cues": [
            "very good", "high quality", "convenient", "cost-effective",
            "value for money", "highly recommended", "good choice",
        ],
    },
    "Meta / Llama": {
        "tendencies": [
            "casual, conversational filler",
            "repetition of the product name",
            "generic praise with thin detail",
        ],
        "cues": [
            "really", "pretty", "definitely", "honestly", "for sure",
            "tbh", "super", "kinda",
        ],
    },
}


def families_brief() -> str:
    """A compact text block the analyzer can be primed with."""
    lines = []
    for name, info in MODEL_FAMILIES.items():
        lines.append(f"- {name}: " + "; ".join(info["tendencies"]))
    return "\n".join(lines)
