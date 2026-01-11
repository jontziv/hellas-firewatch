# Security & Privacy (MVP)

- No login required; uses a random device fingerprint stored in a cookie.
- IP and device fingerprint are stored hashed.
- Photos are optional; stored locally in `var/photos/`.
- Rate limiting is in-memory; for multi-instance production, move to Redis/D1/Supabase RLS.
