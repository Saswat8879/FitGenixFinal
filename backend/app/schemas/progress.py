from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime
from typing import Any


class WeightLogCreate(BaseModel):
    weight_kg: float
    notes: str | None = None


class WeightLogOut(BaseModel):
    date: str
    weight_kg: float
    bmi: float | None = None


class WeightLogResponse(BaseModel):
    id: int
    weight_kg: float
    bmi: float
    timestamp: datetime
    message: str


class GoalProgress(BaseModel):
    goal: str
    percent: float
    detail: str | None = None
    start_weight: float | None = None
    current_weight: float | None = None
    target_weight: float | None = None
    risk_score: float | None = None
    avg_points: float | None = None


class TrendPoint(BaseModel):
    date: str
    value: float


class LifestylePointsTrend(BaseModel):
    date: str
    total: float
    breakdown: dict | None = None


class PlatformAverage(BaseModel):
    avg_lifestyle_points: float
    active_users: int
