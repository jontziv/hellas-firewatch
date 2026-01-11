# Architecture (Python-first)

## Components
- **API**: FastAPI (serves REST + static web)
- **DB**: SQLite (default) via SQLModel; compatible with Postgres later
- **Frontend**: Leaflet + OSM, vanilla JS
- **Ingestion**: Python scripts (stubbed for MVP; can be scheduled via GitHub Actions/cron)

## Data flow
1. Detections stored in DB (seeded samples in MVP)
2. Frontend requests detections as GeoJSON
3. Users verify (confirm/deny/unsure) → API writes verification + aggregates counts
4. API hides dismissed points based on deny thresholds

## Abuse prevention (MVP)
- Per-IP rate limit (token bucket in memory)
- Duplicate vote prevention per device fingerprint per detection
- Cooldown between verifications per device fingerprint
