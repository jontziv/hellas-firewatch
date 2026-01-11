from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

from sqlmodel import Session, select

from .models import Detection

SEED_DETECTIONS = [
    {"name": "Attica - Mount Hymettus", "lat": 37.969, "lon": 23.798, "confidence": 0.72, "fwi_bucket": 4, "wind_dir_deg": 40},
    {"name": "Thessaloniki - Chortiatis", "lat": 40.594, "lon": 23.091, "confidence": 0.64, "fwi_bucket": 3, "wind_dir_deg": 310},
    {"name": "Achaea - Near Patras", "lat": 38.246, "lon": 21.735, "confidence": 0.58, "fwi_bucket": 2, "wind_dir_deg": 200},
    {"name": "Crete - Near Heraklion", "lat": 35.338, "lon": 25.144, "confidence": 0.81, "fwi_bucket": 5, "wind_dir_deg": 90},
]

def seed_if_empty(session: Session) -> None:
    existing = session.exec(select(Detection).limit(1)).first()
    if existing is not None:
        return

    now = datetime.now(timezone.utc)
    for i, d in enumerate(SEED_DETECTIONS):
        det = Detection(
            id=str(uuid.uuid4()),
            lat=d["lat"],
            lon=d["lon"],
            created_at=now - timedelta(minutes=10 * i),
            confidence=d["confidence"],
            source="seed",
            fwi_bucket=d["fwi_bucket"],
            wind_dir_deg=d["wind_dir_deg"],
        )
        session.add(det)
    session.commit()
