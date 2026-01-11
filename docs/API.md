# API

## GET /api/detections
Query params:
- `hours` (int, default 24)
- `min_confidence` (float, default 0.0)

Returns GeoJSON FeatureCollection.

## POST /api/detections/{id}/verify
Multipart form:
- `verdict`: one of `confirm|deny|unsure`
- `photo`: optional file (image), stored on disk in MVP

Returns updated community counts and detection status.

## GET /api/metrics
Returns:
- north-star metric
- false-alarm rate proxy
- abuse block rate proxy
