# 👻 ghost.reviews

**Paste a product → we pull its reviews from the live web → AI exposes the fakes ("ghost" reviews) → you get a Ghost Score.**

Built for the DeveloperWeek New York 2026 Hackathon. One project, three sponsor challenges:

| Sponsor | How we use it |
|---|---|
| **Nimble** | `ghost/nimble_client.py` pulls **live** review text from across the web via the Nimble Search API (deep mode = real-time webpage extraction). |
| **Tower** | `run_pipeline.py` + `Towerfile` deploy the crawl→score→store pipeline as a serverless Python app, with secrets + scheduling. |
| **name.com** | The product *is* the domain **ghost.reviews** — "ghost" = fake/phantom reviews. The name is the concept. |

---

## How it works

```
  product name
      │
      ▼
 [ Nimble ]   live web → real review text          (ghost/nimble_client.py)
      │
      ▼
 [ Claude ]   scores each review 0–100 "ghost"      (ghost/detector.py)
      │           + red-flag reasons
      ▼
 [ Output ]   Ghost Score + flagged reviews         (ghost/pipeline.py)
      │
      ├── dashboard  → app.py   (the demo)
      └── Tower run  → ghost_results.json / Iceberg lakehouse
```

---

## Quick start (local — for the demo video)

```bash
cd ghost-reviews
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

streamlit run app.py        # runs immediately in free SAMPLE mode — no keys
```

It runs with **zero keys** on built-in sample reviews (the dashboard shows a
"Demo mode" badge). To go live, `cp .env.example .env` and fill in:
- `NIMBLE_API_KEY` → pulls real reviews from the web (badge flips to "Live mode")
- `ANTHROPIC_API_KEY` → upgrades the teardown from the free rule engine to Claude

Type a product, hit **Scan for ghosts**, record the screen. Done.

CLI version (no UI):

```bash
GHOST_PRODUCT="Acme Wireless Earbuds" python -m ghost.pipeline
```

---

## Deploy to Tower (for the Tower challenge)

Each run lands one summary row in the **Iceberg lakehouse** table `ghost_scans`
(via `ghost/lakehouse.py`) — so scheduled re-scans build a history of how each
product's Ghost Score moves over time. That history table is the data-flywheel
the roadmap depends on, and the "data lands in storage" story Tower judges want.

```bash
pip install -U "tower[iceberg]"
tower login

# 1. (once) make sure your account has a default Iceberg catalog
#    Tower dashboard -> Catalogs -> create one if you don't have it.

# 2. store keys as Tower secrets (injected as env vars at runtime)
tower secrets create --name=NIMBLE_API_KEY    --value=...   # optional (live reviews)
tower secrets create --name=ANTHROPIC_API_KEY --value=...   # optional (Claude teardown)

# 3. deploy + run
tower apps create --name=ghost-reviews
tower deploy
tower run --parameter=product="Acme Wireless Earbuds" --parameter=max_results="10"
tower apps logs ghost-reviews#1
```

The run prints `lakehouse: upserted 'Acme Wireless Earbuds' (YYYY-MM-DD) -> ghost_scans`.
Inspect the table from the Tower dashboard (Catalogs → ghost_scans) or with the
read examples in `tower-examples`.

**Schedule it** (daily history): in the Tower dashboard, add a schedule to the
`ghost-reviews` app (e.g. daily) — the write is an upsert keyed on
`(product, scanned_date)`, so same-day re-runs update the row instead of
duplicating it.

> Local runs without a catalog simply skip the lakehouse write and still produce
> `ghost_results.json`, so the demo is unaffected.

---

## Keys you need
- **NIMBLE_API_KEY** — from https://www.nimbleway.com/ dashboard
- **ANTHROPIC_API_KEY** — from the Anthropic console

## Files
- `ghost/nimble_client.py` — live web → reviews (Nimble), with sample fallback
- `ghost/detector.py` — adversarial teardown: human-vs-AI score + reasons + self-written baselines + family preview
- `ghost/model_profiles.py` — how each model family tends to write (the "fingerprint" knowledge)
- `ghost/lakehouse.py` — upserts each scan summary into the Tower Iceberg table `ghost_scans`
- `ghost/pipeline.py` — orchestration + persistence (Tower entry logic)
- `run_pipeline.py` + `Towerfile` — Tower deployment
- `app.py` — Streamlit dashboard (the demo)
