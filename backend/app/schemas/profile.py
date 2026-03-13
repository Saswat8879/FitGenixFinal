from pydantic import BaseModel
from datetime import datetime


class ProfileOut(BaseModel):
    user_id: int
    name: str
    email: str
    age: int | None = None
    sex: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    goal: str | None = None
    diet_type: str | None = None
    equipment: list[str] = []
    time_available_min: int = 30
    coaching_style: str | None = None
    country: str | None = None
    cuisine_preference: str | None = None
    activity_level: str | None = None
    work_style: str | None = None
    preferred_notifications: bool = True
    cluster_archetype: str | None = None
    conditions: dict = {}
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class PersonalUpdate(BaseModel):
    name: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    age: int | None = None


class GoalsUpdate(BaseModel):
    goal: str | None = None
    coaching_style: str | None = None
    time_available_min: int | None = None
    activity_level: str | None = None


class DietUpdate(BaseModel):
    diet_type: str | None = None
    cuisine_preference: str | None = None
    equipment: list[str] | None = None


class ConditionsUpdate(BaseModel):
    type_2_diabetes: bool | None = None
    pre_diabetes: bool | None = None
    hypertension: bool | None = None
    high_cholesterol: bool | None = None
    fatty_liver: bool | None = None
    obesity: bool | None = None
    asthma_copd: bool | None = None
    back_pain: bool | None = None
    knee_pain: bool | None = None
    shoulder_pain: bool | None = None
    family_history_diabetes: bool | None = None
    on_medication: bool | None = None
    doctor_supervised: bool | None = None


class NotificationsUpdate(BaseModel):
    preferred_notifications: bool


class ProfileUpdateResponse(BaseModel):
    message: str
    plans_regenerated: bool = False
    profile: ProfileOut | None = None
