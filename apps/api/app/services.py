from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

from fastapi import UploadFile, HTTPException
from sqlmodel import Session
from sqlmodel import select, func

from .config import settings
from .models import Detection, Verification, Verdict, DetectionStatus
from .repositories import DetectionRepository, VerificationRepository


@dataclass(frozen=True)
class AggregatedCounts:
    confirms: int
    denies: int
    unsure: int

    def as_dict(self) -> Dict[str, int]:
        return {"confirms": self.confirms, "denies": self.denies, "unsure": self.unsure}


class PhotoStorage:
    def __init__(self, photos_dir: str) -> None:
        self.photos_dir = photos_dir
        os.makedirs(self.photos_dir, exist_ok=True)

    async def save(self, file: UploadFile) -> str:
        ct = (file.content_type or "").lower()
        if ct not in {"image/jpeg", "image/jpg", "image/png", "image/webp"}:
            raise HTTPException(status_code=400, detail="Photo must be jpeg/png/webp.")
        ext = ".jpg" if "jpeg" in ct or "jpg" in ct else ".png" if "png" in ct else ".webp"
        name = secrets.token_hex(16) + ext
        path = os.path.join(self.photos_dir, name)

        data = await file.read()
        if len(data) > 4 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Photo too large (max 4MB).")

        with open(path, "wb") as f:
            f.write(data)
        return path


class VerificationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.detections = DetectionRepository(session)
        self.verifications = VerificationRepository(session)
        self.photos = PhotoStorage(settings.photos_dir)

    def _evaluate_status(self, counts: AggregatedCounts) -> DetectionStatus:
        # MVP rule:
        # - accepted if >= 1 confirm
        # - dismissed if denies >= threshold AND (optional) denies > confirms
        if counts.confirms >= 1:
            return DetectionStatus.accepted
        if counts.denies >= settings.dismiss_deny_threshold:
            if settings.dismiss_deny_over_confirm:
                if counts.denies > counts.confirms:
                    return DetectionStatus.dismissed
            else:
                return DetectionStatus.dismissed
        return DetectionStatus.unconfirmed

    def get_counts(self, detection_id: str) -> AggregatedCounts:
        c, d, u = self.verifications.counts(detection_id)
        return AggregatedCounts(confirms=c, denies=d, unsure=u)

    async def submit(
        self,
        detection_id: str,
        verdict: Verdict,
        device_fp_hash: str,
        ip_hash: str,
        photo: Optional[UploadFile] = None,
    ) -> Tuple[Detection, AggregatedCounts]:
        det = self.detections.get(detection_id)
        if det is None:
            raise HTTPException(status_code=404, detail="Detection not found.")
        if det.status == DetectionStatus.dismissed:
            raise HTTPException(status_code=410, detail="Detection already dismissed.")
        if self.verifications.exists_for_device(detection_id, device_fp_hash):
            raise HTTPException(status_code=409, detail="You already verified this detection.")

        photo_path: Optional[str] = None
        if photo is not None and settings.save_photos:
            photo_path = await self.photos.save(photo)

        v = Verification(
            detection_id=detection_id,
            created_at=datetime.now(timezone.utc),
            verdict=verdict,
            device_fp_hash=device_fp_hash,
            ip_hash=ip_hash,
            photo_path=photo_path,
        )
        self.verifications.add(v)

        counts = self.get_counts(detection_id)
        new_status = self._evaluate_status(counts)
        if new_status != det.status:
            det = self.detections.set_status(det, new_status)

        return det, counts


class MetricsService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.detections = DetectionRepository(session)
        self.verifications = VerificationRepository(session)

    def compute(self, window_hours: int = 24) -> Dict[str, float | Dict[str, int]]:
        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=window_hours)

        dets = self.detections.list_recent(hours=window_hours, min_confidence=0.0, include_dismissed=True)
        total = len(dets)
        if total == 0:
            return {
                "north_star_pct": 0.0,
                "false_alarm_rate": 0.0,
                "abuse_block_rate": 0.0,
                "totals": {"detections": 0, "dismissed": 0, "accepted": 0, "verifications": 0},
            }

        north_ok = 0
        dismissed = 0
        accepted = 0

        for d in dets:
            if d.status == DetectionStatus.dismissed:
                dismissed += 1
            if d.status == DetectionStatus.accepted:
                accepted += 1

            start = d.created_at
            end = d.created_at + timedelta(minutes=30)
            from .models import Verification
            stmt = select(func.count(Verification.id)).where(
                Verification.detection_id == d.id,
                Verification.created_at >= start,
                Verification.created_at <= end,
            )
            c = int(self.session.exec(stmt).one())
            if c >= 3:
                north_ok += 1

        from .security import abuse_stats
        attempts, blocked = abuse_stats()
        abuse_rate = (blocked / attempts) if attempts else 0.0

        false_alarm = dismissed / total
        verif_total = self.verifications.count_total_in_window(since)

        return {
            "north_star_pct": (north_ok / total) * 100.0,
            "false_alarm_rate": float(false_alarm),
            "abuse_block_rate": float(abuse_rate),
            "totals": {"detections": total, "dismissed": dismissed, "accepted": accepted, "verifications": verif_total},
        }
