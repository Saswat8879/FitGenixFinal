from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime


class MealFromPlan(BaseModel):
    diet_plan_id: int
    food_id: int | None = None
    food_name: str | None = None
    meal_slot: str
    portion_g: float = 100
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    sodium_mg: float | None = None
    sugar_g: float | None = None
    saturated_fat_g: float | None = None
    timestamp: datetime | None = None


class MealSearch(BaseModel):
    query: str
    meal_slot: str = "other"
    timestamp: datetime | None = None


class MealSearchResult(BaseModel):
    name: str
    source: str = "local_db"
    calories: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0
    food_id: int | None = None


class MealConfirm(BaseModel):
    name: str
    meal_slot: str
    portion_g: float
    calories: float
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0
    sodium_mg: float = 0
    sugar_g: float = 0
    saturated_fat_g: float = 0
    timestamp: datetime | None = None


class MealCustom(BaseModel):
    food_name: str
    meal_slot: str
    portion_g: float = 100
    calories: float
    protein: float = 0
    carbs: float = 0
    fat: float = 0
    fiber: float = 0
    sodium: float = 0
    sugar: float = 0
    saturated_fat: float = 0
    timestamp: datetime | None = None


class MealLogOut(BaseModel):
    id: int
    timestamp: datetime | None = None
    food_name: str | None = None
    meal_slot: str
    portion_g: float
    calories: float = 0
    protein: float = 0
    carbs: float = 0
    fat: float = 0
    fiber: float = 0
    source: str = "manual"

    class Config:
        from_attributes = True


class WaterLogCreate(BaseModel):
    amount_ml: float
    source: str | None = None
    timestamp: datetime | None = None


class WaterLogOut(BaseModel):
    id: int
    timestamp: datetime
    amount_ml: float
    source: str = "manual"

    class Config:
        from_attributes = True


class WaterTodayOut(BaseModel):
    total_ml: float
    target_ml: float
    log_count: int = 0
