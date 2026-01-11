from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field

from .models import Verdict


class DetectionCounts(BaseModel):
    confirms: int
    denies: int
    unsure: int


class MetricsResponse(BaseModel):
    window_hours: int = Field(default=24)
    north_star_pct: float
    false_alarm_rate: float
    abuse_block_rate: float
    totals: Dict[str, Any]
