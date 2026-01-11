# Data Model

## Detection
- id (uuid string)
- lat, lon
- created_at (utc)
- confidence (0..1)
- source (string)
- fwi_bucket (0..5) (placeholder for EFFIS FWI)
- wind_dir_deg (0..359)
- status: unconfirmed|accepted|dismissed

## Verification
- id (int)
- detection_id
- created_at (utc)
- verdict (confirm/deny/unsure)
- device_fp_hash (sha256)
- ip_hash (sha256)
- photo_path (optional)
