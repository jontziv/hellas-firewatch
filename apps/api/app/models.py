from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import String


class Verdict(str, Enum):
    confirm = "confirm"
    deny = "deny"
    unsure = "unsure"


class DetectionStatus(str, Enum):
    unconfirmed = "unconfirmed"
    accepted = "accepted"
    dismissed = "dismissed"


class Detection(SQLModel, table=True):
    id: str = Field(sa_column=Column(String, primary_key=True))
    lat: float
    lon: float
    created_at: datetime = Field(index=True)
    confidence: float = Field(index=True)
    source: str = Field(default="seed")
    fwi_bucket: int = Field(default=2)       # 0..5 placeholder for MVP
    wind_dir_deg: int = Field(default=0)     # 0..359
    status: DetectionStatus = Field(default=DetectionStatus.unconfirmed, index=True)


class Verification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    detection_id: str = Field(index=True, foreign_key="detection.id")
    created_at: datetime = Field(index=True)
    verdict: Verdict = Field(index=True)
    device_fp_hash: str = Field(index=True)
    ip_hash: str = Field(index=True)
    photo_path: Optional[str] = Field(default=None)
