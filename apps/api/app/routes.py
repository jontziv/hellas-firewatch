from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlmodel import Session

from .db import get_session
from .geojson import detections_to_feature_collection
from .models import Verdict
from .repositories import DetectionRepository
from .schemas import MetricsResponse
from .security import (
    sha256_hex,
    device_fingerprint_raw,
    get_client_ip,
    enforce_rate_limit,
    enforce_cooldown,
    record_attempt,
)
from .services import VerificationService, MetricsService

router = APIRouter(prefix="/api")


def session_dep() -> Session:
    return get_session()


@router.get("/detections")
def list_detections(hours: int = 24, min_confidence: float = 0.0, session: Session = Depends(session_dep)):
    repo = DetectionRepository(session)
    dets = repo.list_recent(hours=hours, min_confidence=min_confidence, include_dismissed=False)

    vs = VerificationService(session)
    enriched = [{"detection": d, "counts": vs.get_counts(d.id).as_dict()} for d in dets]
    return detections_to_feature_collection(enriched)


@router.post("/detections/{detection_id}/verify")
async def verify_detection(
    detection_id: str,
    request: Request,
    verdict: Verdict = Form(...),
    photo: Optional[UploadFile] = File(default=None),
    session: Session = Depends(session_dep),
):
    record_attempt()
    enforce_rate_limit(request)

    fp_raw = device_fingerprint_raw(request)
    device_fp_hash = sha256_hex(fp_raw)
    enforce_cooldown(device_fp_hash)

    ip_hash = sha256_hex(get_client_ip(request))

    svc = VerificationService(session)
    det, counts = await svc.submit(
        detection_id=detection_id,
        verdict=verdict,
        device_fp_hash=device_fp_hash,
        ip_hash=ip_hash,
        photo=photo,
    )
    return {"id": det.id, "status": det.status.value, "counts": counts.as_dict()}


@router.get("/metrics", response_model=MetricsResponse)
def metrics(window_hours: int = 24, session: Session = Depends(session_dep)):
    svc = MetricsService(session)
    m = svc.compute(window_hours=window_hours)
    return MetricsResponse(
        window_hours=window_hours,
        north_star_pct=float(m["north_star_pct"]),
        false_alarm_rate=float(m["false_alarm_rate"]),
        abuse_block_rate=float(m["abuse_block_rate"]),
        totals=m["totals"],  # type: ignore[arg-type]
    )
