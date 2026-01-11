# hellas-firewatch (Python MVP)

A minimal, production-ready MVP for community verification of wildfire detections in Greece.

---
title: Hellas Firewatch
emoji: 🔥
colorFrom: orange
colorTo: red
sdk: docker
app_port: 7860
---

## What you get
- FastAPI backend (SQLite by default; easy to switch to Postgres/Supabase later)
- Leaflet + OpenStreetMap frontend (no paid maps, no Node build step)
- 4 seeded **unconfirmed** detections (different Greek regions)
- Click a detection → confirm/deny/unsure (optional photo) → map updates
- Basic abuse prevention (rate-limits + duplicate vote blocking per device fingerprint)
- Metrics endpoint for the north-star metric

## Quickstart (local)

### 1) Create venv & install
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Run the API (also serves the web UI)
```bash
uvicorn apps.api.app.main:app --reload --port 8000
```

Open: http://127.0.0.1:8000

## Endpoints
- `GET /api/detections` → GeoJSON features (last 24h by default)
- `POST /api/detections/{id}/verify` → submit verification
- `GET /api/metrics` → north-star metric + guardrails (basic)

## Config
Environment variables:
- `HF_DB_URL` (default: `sqlite:///./var/app.db`)
- `HF_RATE_LIMIT_PER_MINUTE` (default: `30`)
- `HF_VERIFY_COOLDOWN_SECONDS` (default: `30`)
- `HF_DISMISS_DENY_THRESHOLD` (default: `2`)
- `HF_DISMISS_DENY_OVER_CONFIRM` (default: `True`)

## Repo layout
- `apps/api` – FastAPI app
- `apps/web` – static frontend (Leaflet)
- `docs/` – PRD/ARCH/API/etc (starter docs)
