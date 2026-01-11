from __future__ import annotations

from typing import Any, Dict, List

from .models import Detection


def detections_to_feature_collection(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    features = []
    for it in items:
        d: Detection = it["detection"]
        counts = it["counts"]
        features.append(
            {
                "type": "Feature",
                "id": d.id,
                "geometry": {"type": "Point", "coordinates": [d.lon, d.lat]},
                "properties": {
                    "id": d.id,
                    "created_at": d.created_at.isoformat(),
                    "confidence": d.confidence,
                    "source": d.source,
                    "fwi_bucket": d.fwi_bucket,
                    "wind_dir_deg": d.wind_dir_deg,
                    "status": d.status.value,
                    "community": counts,
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}
