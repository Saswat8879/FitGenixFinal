from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime


class StressOut(BaseModel):
    stress_level: float
    is_stressed: bool
    method: str = "ml"
    interventions: list[str] = []
    timestamp: datetime | None = None


class LifestyleCheckin(BaseModel):
    mood: int | None = None
    sleep_hours: float | None = None
    sleep_quality: int | None = None
    stress_self_report: float | None = None
    hydration_ml: float | None = None
    sedentary_minutes: int | None = None
    posture_alert: bool | None = None
    timestamp: datetime | None = None


class LifestyleCheckinOut(BaseModel):
    id: int
    timestamp: datetime | None = None
    mood: int | None = None
    sleep_hours: float | None = None
    sleep_quality: int | None = None
    stress_level: float | None = None
    is_stressed: bool = False
    hydration_ml: float | None = None
    sedentary_minutes: int | None = None
    stress_interventions: list[str] = []
    message: str | None = None

    class Config:
        from_attributes = True


class TipsOut(BaseModel):
    tips: list[str]


class PostureOut(BaseModel):
    alert: bool
    sedentary_minutes: int
    message: str = ""
