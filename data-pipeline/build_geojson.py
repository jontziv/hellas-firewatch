"""Export detections from DB to GeoJSON (optional)."""

from __future__ import annotations

import json
from pathlib import Path
from sqlmodel import Session

from apps.api.app.db import engine
from apps.api.app.repositories import DetectionRepository
from apps.api.app.services import VerificationService
from apps.api.app.geojson import detections_to_feature_collection


def export(path: str = "public/data/detections.geojson", hours: int = 24) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with Session(engine) as s:
        repo = DetectionRepository(s)
        items = repo.list_recent(hours=hours, min_confidence=0.0, include_dismissed=False)
        vs = VerificationService(s)
        enriched = [{"detection": d, "counts": vs.get_counts(d.id).as_dict()} for d in items]
        fc = detections_to_feature_collection(enriched)
    p.write_text(json.dumps(fc, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    export()
