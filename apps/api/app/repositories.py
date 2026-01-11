from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlmodel import Session, select, func

from .models import Detection, Verification, Verdict, DetectionStatus


class DetectionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_recent(self, hours: int, min_confidence: float, include_dismissed: bool = False) -> List[Detection]:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        stmt = select(Detection).where(Detection.created_at >= since, Detection.confidence >= min_confidence)
        if not include_dismissed:
            stmt = stmt.where(Detection.status != DetectionStatus.dismissed)
        stmt = stmt.order_by(Detection.created_at.desc())
        return list(self.session.exec(stmt))

    def get(self, detection_id: str) -> Optional[Detection]:
        stmt = select(Detection).where(Detection.id == detection_id)
        return self.session.exec(stmt).first()

    def set_status(self, detection: Detection, status: DetectionStatus) -> Detection:
        detection.status = status
        self.session.add(detection)
        self.session.commit()
        self.session.refresh(detection)
        return detection


class VerificationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def exists_for_device(self, detection_id: str, device_fp_hash: str) -> bool:
        stmt = select(Verification.id).where(
            Verification.detection_id == detection_id, Verification.device_fp_hash == device_fp_hash
        )
        return self.session.exec(stmt).first() is not None

    def add(self, v: Verification) -> Verification:
        self.session.add(v)
        self.session.commit()
        self.session.refresh(v)
        return v

    def counts(self, detection_id: str) -> Tuple[int, int, int]:
        stmt = (
            select(Verification.verdict, func.count(Verification.id))
            .where(Verification.detection_id == detection_id)
            .group_by(Verification.verdict)
        )
        rows = list(self.session.exec(stmt))
        counts = {Verdict.confirm: 0, Verdict.deny: 0, Verdict.unsure: 0}
        for verdict, c in rows:
            counts[verdict] = int(c)
        return counts[Verdict.confirm], counts[Verdict.deny], counts[Verdict.unsure]

    def count_total_in_window(self, since: datetime) -> int:
        stmt = select(func.count(Verification.id)).where(Verification.created_at >= since)
        return int(self.session.exec(stmt).one())
