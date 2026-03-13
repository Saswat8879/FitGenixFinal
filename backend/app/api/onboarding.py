"""Onboarding: submit survey → create profile, conditions, compute embedding, generate plans."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, Profile, Condition
from app.schemas.onboarding import OnboardingSurvey, OnboardingResponse
from app.api.deps import get_current_user
from app.services.personalization_service import compute_user_embedding
from app.services.risk_service import compute_diabetes_risk
from app.services.plan_service import generate_workout, generate_diet_plan

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.post("/survey", response_model=OnboardingResponse)
def submit_survey(
    body: OnboardingSurvey,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Upsert Profile
    profile = user.profile
    if not profile:
        profile = Profile(user_id=user.id)
        db.add(profile)

    for field in [
        "age", "sex", "height_cm", "weight_kg", "goal", "diet_type",
        "equipment", "time_available_min", "coaching_style", "country",
        "cuisine_preference", "activity_level", "work_style",
    ]:
        val = getattr(body, field, None)
        if val is not None:
            setattr(profile, field, val)

    # Upsert Conditions
    cond = user.conditions
    if not cond:
        cond = Condition(user_id=user.id)
        db.add(cond)

    for field in [
        "type_2_diabetes", "pre_diabetes", "hypertension", "high_cholesterol",
        "fatty_liver", "obesity", "asthma_copd", "back_pain", "knee_pain",
        "shoulder_pain", "family_history_diabetes", "on_medication", "doctor_supervised",
    ]:
        val = getattr(body, field, None)
        if val is not None:
            setattr(cond, field, val)

    db.commit()
    db.refresh(user)

    # Compute embedding + cluster
    embedding_result = compute_user_embedding(user, db)

    # Diabetes risk
    risk_result = compute_diabetes_risk(user, db)

    # Generate initial plans
    workout = generate_workout(user, db)
    diet = generate_diet_plan(user, db)

    return OnboardingResponse(
        message="Onboarding complete",
        cluster_id=user.cluster_id,
        cluster_archetype=user.cluster_archetype,
        diabetes_risk=risk_result.get("risk_category", "Unknown"),
        workout_id=workout.id,
        diet_plan_id=diet.id,
    )
