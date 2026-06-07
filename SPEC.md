# ghost.reviews — LOCKED SPEC (do not relitigate)

## What it is
A tool that takes a product (e.g. an Amazon listing with lots of reviews),
pulls its reviews from the live web, and tells the user which reviews are
written by **real humans** vs **AI ghostwriters** — and whether the AI reviews
are steering the rating up (astroturfing) or down (bombing), so the user knows
whether to trust the product.

## The 3 sponsor items (one app hits all three)
1. **name.com** → the domain / name: **ghost.reviews**
2. **Nimble** → pulls the live reviews from the web
3. **Tower** → runs the analysis pipeline + stores results

## The engine — ONE analyzing AI (NOT multiple live models, NO OpenRouter)
The single analyzing model does three things:
1. **Knows how each model family writes** — a built-in knowledge base of the
   behavioral "fingerprints" of GPT/Copilot, Gemini, Claude, DeepSeek, Qwen,
   Meta. (`ghost/model_profiles.py`) It reasons WITH this knowledge.
2. **Adversarially rips each review apart** — tears down the wording to judge
   whether a human or an AI wrote it.
3. **Writes its own review of the product** and compares the suspect review
   against that self-written baseline.

## Output
- **Human vs AI** per review (works today).
- **Closest model family** = a clearly-labeled **PREVIEW / roadmap** feature.
  Family-level only (e.g. "Gemini", never "Gemini 3.5"). Always shown as a
  confidence/probability, NEVER claimed as certainty. It is the data-flywheel
  vision, not a solved feature.
- A **trust verdict**: Buy it / Be careful / Avoid, with the human-vs-AI
  rating gap ("listed 4.1★, real humans 3.2★").

## Hard constraints (locked)
- ONE model. Do NOT call 6 separate live models. Do NOT use OpenRouter.
- The model-family knowledge base (`model_profiles.py`) STAYS — it is core.
- Runs FREE on a rule engine; optional single Anthropic key upgrades quality.
- Participation is ONLINE ONLY → optimize for the 3 sponsor challenges, not the
  in-person Overall pitch.
- Honest framing on attribution: preview/roadmap, family-level, probability.

## Deadline
Wed June 10, 2026 @ 10:00 AM EST. Submit on https://dwny-2026-hackathon.devpost.com/
