"""Plans: workout + diet plan generation, retrieval, feedback."""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.plan import Workout, DietPlan
from app.schemas.plans import WorkoutOut, WorkoutFeedback, DietPlanOut, RegeneratePlansRequest
from app.api.deps import get_current_user
from app.services.plan_service import (
    generate_workout,
    generate_diet_plan,
    get_diet_targets,
    DIET_PLAN_GENERATOR_VERSION,
)
from app.services.lifestyle_points_service import force_recompute
from app.utils.timing_utils import ist_start_of_day, ist_end_of_day

router = APIRouter(prefix="/plans", tags=["Plans"])


def _is_legacy_diet_plan(plan: DietPlan | None) -> bool:
    if not plan or not isinstance(plan.meals_json, dict):
        return True
    meta = plan.meals_json.get("_meta", {}) if isinstance(plan.meals_json, dict) else {}
    return meta.get("generator_version") != DIET_PLAN_GENERATOR_VERSION


@router.get("/workout/today", response_model=WorkoutOut)
def get_today_workout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    start, end = ist_start_of_day(today), ist_end_of_day(today)
    workout = db.query(Workout).filter(
        Workout.user_id == user.id,
        Workout.date.between(start, end),
    ).order_by(Workout.date.desc(), Workout.id.desc()).first()
    if (not workout) or (not workout.exercises) or (len(workout.exercises) == 0):
        workout = generate_workout(user, db, today)
    return _workout_out(workout)


@router.get("/workout/{workout_id}", response_model=WorkoutOut)
def get_workout(workout_id: int, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    workout = db.query(Workout).filter(
        Workout.id == workout_id, Workout.user_id == user.id
    ).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return _workout_out(workout)


@router.post("/workout/{workout_id}/complete", response_model=WorkoutOut)
def complete_workout(workout_id: int, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    workout = db.query(Workout).filter(
        Workout.id == workout_id, Workout.user_id == user.id
    ).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    from datetime import datetime, timezone
    workout.status = "completed"
    workout.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(workout)
    force_recompute(user, db)
    return _workout_out(workout)


@router.post("/workout/{workout_id}/feedback", response_model=WorkoutOut)
def submit_workout_feedback(workout_id: int, body: WorkoutFeedback,
                            user: User = Depends(get_current_user),
                            db: Session = Depends(get_db)):
    workout = db.query(Workout).filter(
        Workout.id == workout_id, Workout.user_id == user.id
    ).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    workout.feedback_json = body.model_dump()
    db.commit()
    db.refresh(workout)
    return _workout_out(workout)


@router.get("/diet/today", response_model=DietPlanOut)
def get_today_diet(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    start, end = ist_start_of_day(today), ist_end_of_day(today)
    plan = db.query(DietPlan).filter(
        DietPlan.user_id == user.id,
        DietPlan.date.between(start, end),
    ).order_by(DietPlan.date.desc(), DietPlan.id.desc()).first()
    if (not plan) or (not plan.meals_json) or (len(plan.meals_json) == 0) or _is_legacy_diet_plan(plan):
        plan = generate_diet_plan(user, db, today)
    return _diet_out(plan, user)


@router.get("/diet/{plan_id}", response_model=DietPlanOut)
def get_diet_plan(plan_id: int, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    plan = db.query(DietPlan).filter(
        DietPlan.id == plan_id, DietPlan.user_id == user.id
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Diet plan not found")
    return _diet_out(plan, user)


@router.post("/regenerate")
def regenerate_plans(body: RegeneratePlansRequest, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    results = {}
    today = date.today()
    if body.workout:
        workout = generate_workout(user, db, today)
        results["workout_id"] = workout.id
    if body.diet:
        diet = generate_diet_plan(user, db, today)
        results["diet_plan_id"] = diet.id
    return {"message": "Plans regenerated", **results}


def _workout_out(w: Workout) -> WorkoutOut:
    d = w.date.date() if hasattr(w.date, "date") else w.date
    return WorkoutOut(
        id=w.id,
        date=str(d) if d else None,
        exercises=w.exercises or [],
        status=w.status,
        completed_at=w.completed_at,
        feedback=w.feedback_json,
        source=w.source,
    )


def _diet_out(p: DietPlan, user: User | None = None) -> DietPlanOut:
    d = p.date.date() if hasattr(p.date, "date") else p.date
    meals = p.meals_json or {}
    meta = meals.get("_meta", {}) if isinstance(meals, dict) else {}
    if user:
        targets = get_diet_targets(user)
    else:
        targets = {
            "calorie_target": meta.get("calorie_target"),
            "protein_target_g": meta.get("protein_target_g"),
            "carbs_target_g": meta.get("carbs_target_g"),
            "fat_target_g": meta.get("fat_target_g"),
            "fiber_target_g": meta.get("fiber_target_g"),
            "bmr": meta.get("bmr"),
            "tdee": meta.get("tdee"),
        }

    total_fiber = 0.0
    if isinstance(meals, dict):
        for slot_items in meals.values():
            if not isinstance(slot_items, list):
                continue
            for item in slot_items:
                total_fiber += float(item.get("fiber_g", 0) or 0)

    return DietPlanOut(
        id=p.id,
        date=str(d) if d else None,
        meals=meals,
        total_calories=p.total_calories,
        total_protein=p.total_protein,
        total_carbs=p.total_carbs,
        total_fat=p.total_fat,
        total_fiber_g=round(total_fiber, 1),
        total_sodium=p.total_sodium,
        calorie_target=targets.get("calorie_target"),
        protein_target_g=targets.get("protein_target_g"),
        carbs_target_g=targets.get("carbs_target_g"),
        fat_target_g=targets.get("fat_target_g"),
        fiber_target_g=targets.get("fiber_target_g"),
        bmr=targets.get("bmr"),
        tdee=targets.get("tdee"),
        adherence_score=p.adherence_score,
        source=p.source,
    )
