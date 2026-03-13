from __future__ import annotations

from pydantic import BaseModel


class DashboardOut(BaseModel):
    user_name: str
    cluster_archetype: str | None = None
    bmi: float | None = None
    diabetes_risk: str | None = None
    diabetes_risk_score: float | None = None
    cvd_risk_score: float | None = None
    metrics: dict | None = None
    lifestyle_points: float = 0
    lifestyle_breakdown: dict | None = None
    workout_status: str = "no_plan"
    workout_exercise_count: int = 0
    diet_plan_calories: float | None = None
    diet_adherence: float | None = None
    calories_consumed: float = 0
    calorie_target: float | None = None
    water_ml: float = 0
    water_target_ml: float | None = None
    weight_kg: float | None = None
    stress_level: float | None = None
    workout: dict | None = None
    diet: dict | None = None


class DashboardTrends(BaseModel):
    lifestyle_points: list[dict] = []
    calories: list[dict] = []
