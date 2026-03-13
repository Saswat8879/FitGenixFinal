from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime


class WorkoutOut(BaseModel):
    id: int
    date: str | None = None
    exercises: list[dict] = []
    status: str = "pending"
    completed_at: datetime | None = None
    feedback: dict | None = None
    source: str = "ml"

    class Config:
        from_attributes = True


class WorkoutFeedback(BaseModel):
    workout_id: int
    completed: bool
    difficulty_rating: int | None = None
    notes: str | None = None
    exercises_completed: list[dict] | None = None


class DietPlanOut(BaseModel):
    id: int
    date: str | None = None
    meals: dict = {}
    total_calories: float = 0
    total_protein: float = 0
    total_carbs: float = 0
    total_fat: float = 0
    total_fiber_g: float = 0
    total_sodium: float = 0
    calorie_target: float | None = None
    protein_target_g: float | None = None
    carbs_target_g: float | None = None
    fat_target_g: float | None = None
    fiber_target_g: float | None = None
    bmr: float | None = None
    tdee: float | None = None
    adherence_score: float = 0
    source: str = "ml"

    class Config:
        from_attributes = True


class RegeneratePlansRequest(BaseModel):
    workout: bool = True
    diet: bool = True
