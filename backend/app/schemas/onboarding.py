from pydantic import BaseModel


class OnboardingSurvey(BaseModel):
    # Personal
    age: int
    sex: str
    height_cm: float
    weight_kg: float
    country: str | None = None

    # Goals
    goal: str
    diet_type: str
    coaching_style: str = "moderate"
    activity_level: str = "sedentary"
    work_style: str | None = None
    time_available_min: int = 30
    cuisine_preference: str | None = None
    equipment: list[str] = []

    # Conditions
    type_2_diabetes: bool = False
    pre_diabetes: bool = False
    hypertension: bool = False
    high_cholesterol: bool = False
    fatty_liver: bool = False
    obesity: bool = False
    asthma_copd: bool = False
    back_pain: bool = False
    knee_pain: bool = False
    shoulder_pain: bool = False
    family_history_diabetes: bool = False
    on_medication: bool = False
    doctor_supervised: bool = False

    # Notifications
    preferred_notifications: bool = True


class OnboardingResponse(BaseModel):
    message: str
    cluster_id: int | None = None
    cluster_archetype: str | None = None
    diabetes_risk: str | None = None
    workout_id: int | None = None
    diet_plan_id: int | None = None
