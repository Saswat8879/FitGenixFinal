"""Profile view and partial updates."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, Profile, Condition
from app.schemas.profile import (
    ProfileOut, PersonalUpdate, GoalsUpdate, DietUpdate,
    ConditionsUpdate, NotificationsUpdate, ProfileUpdateResponse,
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/", response_model=ProfileOut)
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = user.profile
    cond = user.conditions
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Complete onboarding first.")

    cond_dict = {}
    if cond:
        for f in ["type_2_diabetes", "pre_diabetes", "hypertension", "high_cholesterol",
                   "fatty_liver", "obesity", "asthma_copd", "back_pain", "knee_pain",
                   "shoulder_pain", "family_history_diabetes", "on_medication", "doctor_supervised"]:
            cond_dict[f] = getattr(cond, f, False)

    return ProfileOut(
        user_id=user.id,
        name=user.name,
        email=user.email,
        age=profile.age,
        sex=profile.sex,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        goal=profile.goal.value if profile.goal else None,
        diet_type=profile.diet_type.value if profile.diet_type else None,
        equipment=profile.equipment,
        time_available_min=profile.time_available_min,
        coaching_style=profile.coaching_style.value if profile.coaching_style else None,
        country=profile.country,
        cuisine_preference=profile.cuisine_preference,
        activity_level=profile.activity_level.value if profile.activity_level else None,
        work_style=profile.work_style.value if profile.work_style else None,
        preferred_notifications=profile.preferred_notifications,
        conditions=cond_dict,
        cluster_archetype=user.cluster_archetype,
    )


@router.patch("/personal", response_model=ProfileUpdateResponse)
def update_personal(body: PersonalUpdate, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    profile = user.profile or Profile(user_id=user.id)
    if not user.profile:
        db.add(profile)
    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "name":
            user.name = value
        else:
            setattr(profile, field, value)
    db.commit()
    return ProfileUpdateResponse(message="Personal info updated")


@router.patch("/goals", response_model=ProfileUpdateResponse)
def update_goals(body: GoalsUpdate, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    profile = user.profile
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    # Re-cluster
    from app.services.personalization_service import compute_user_embedding
    compute_user_embedding(user, db)
    return ProfileUpdateResponse(message="Goals updated, re-clustered")


@router.patch("/diet", response_model=ProfileUpdateResponse)
def update_diet(body: DietUpdate, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    profile = user.profile
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    return ProfileUpdateResponse(message="Diet preferences updated")


@router.patch("/conditions", response_model=ProfileUpdateResponse)
def update_conditions(body: ConditionsUpdate, user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    cond = user.conditions
    if not cond:
        cond = Condition(user_id=user.id)
        db.add(cond)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(cond, field, value)
    db.commit()
    return ProfileUpdateResponse(message="Conditions updated")


@router.patch("/notifications", response_model=ProfileUpdateResponse)
def update_notifications(body: NotificationsUpdate, user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    profile = user.profile
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile.preferred_notifications = body.preferred_notifications
    db.commit()
    return ProfileUpdateResponse(message="Notification preference updated")
