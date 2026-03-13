from pydantic import BaseModel
from datetime import datetime


class HealthMetricOut(BaseModel):
    bmi: float | None = None
    weight_kg: float | None = None
    diabetes_risk_score: float | None = None
    diabetes_risk_category: str | None = None
    cvd_risk_score: float | None = None
    stress_level: float | None = None
    resting_hr: float | None = None
    avg_daily_steps: float | None = None
    avg_active_minutes: float | None = None
    avg_sleep_hours: float | None = None
    timestamp: datetime | None = None

    class Config:
        from_attributes = True


class RiskOut(BaseModel):
    risk_type: str
    score: float | None = None
    category: str | None = None
    method: str = "ensemble"
