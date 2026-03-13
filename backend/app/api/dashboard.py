"""Dashboard: unified snapshot of user's daily state."""
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from app.database import get_db
from app.models.user import User
from app.models.plan import Workout, DietPlan
from app.models.logs import MealLog, WaterLog
from app.models.lifestyle import LifestyleLog
from app.models.progress import HealthMetric, LifestylePoint
from app.schemas.dashboard import DashboardOut, DashboardTrends
from app.api.deps import get_current_user
from app.services.progress_service import get_lifestyle_points_trend, get_calorie_trend
from app.services.plan_service import (
    get_diet_targets,
    generate_workout,
    generate_diet_plan,
    DIET_PLAN_GENERATOR_VERSION,
)
from app.utils.timing_utils import ist_start_of_day, ist_end_of_day

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _is_legacy_diet_plan(plan: DietPlan | None) -> bool:
    if not plan or not isinstance(plan.meals_json, dict):
        return True
    meta = plan.meals_json.get("_meta", {}) if isinstance(plan.meals_json, dict) else {}
    return meta.get("generator_version") != DIET_PLAN_GENERATOR_VERSION


@router.get("/", response_model=DashboardOut)
def get_dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    start, end = ist_start_of_day(today), ist_end_of_day(today)

    # Latest health metric
    hm = db.query(HealthMetric).filter(
        HealthMetric.user_id == user.id
    ).order_by(HealthMetric.timestamp.desc()).first()

    # Today's workout
    workout = db.query(Workout).filter(
        Workout.user_id == user.id,
        Workout.date.between(start, end),
    ).order_by(Workout.date.desc(), Workout.id.desc()).first()
    if (not workout) or (not workout.exercises) or (len(workout.exercises) == 0):
        workout = generate_workout(user, db, today)

    # Today's diet plan
    diet = db.query(DietPlan).filter(
        DietPlan.user_id == user.id,
        DietPlan.date.between(start, end),
    ).order_by(DietPlan.date.desc(), DietPlan.id.desc()).first()
    if (not diet) or (not diet.meals_json) or (len(diet.meals_json) == 0) or _is_legacy_diet_plan(diet):
        diet = generate_diet_plan(user, db, today)

    # Today's meal logs (source of truth for consumed nutrition).
    meals = db.query(MealLog).filter(
        MealLog.user_id == user.id,
        MealLog.timestamp.between(start, end),
    ).all()

    calories_consumed = round(sum(m.calories_logged or 0 for m in meals), 1)
    protein_consumed = round(sum(m.protein_logged or 0 for m in meals), 1)
    carbs_consumed = round(sum(m.carbs_logged or 0 for m in meals), 1)
    fat_consumed = round(sum(m.fat_logged or 0 for m in meals), 1)
    fiber_consumed = round(sum(m.fiber_logged or 0 for m in meals), 1)

    # Today's water logs.
    water_ml = db.query(sa_func.sum(WaterLog.amount_ml)).filter(
        WaterLog.user_id == user.id,
        WaterLog.timestamp.between(start, end),
    ).scalar() or 0.0

    # Latest stress sample for today.
    stress_log = db.query(LifestyleLog).filter(
        LifestyleLog.user_id == user.id,
        LifestyleLog.timestamp.between(start, end),
        LifestyleLog.stress_level.isnot(None),
    ).order_by(LifestyleLog.timestamp.desc()).first()

    targets = get_diet_targets(user)
    weight_kg = (user.profile.weight_kg if user.profile and user.profile.weight_kg else None)
    water_target_ml = round((weight_kg or 70) * 35)

    meals_planned = 0
    if diet and isinstance(diet.meals_json, dict):
        for slot_items in diet.meals_json.values():
            if isinstance(slot_items, list):
                meals_planned += len(slot_items)

    duration_minutes = 0
    if workout and workout.exercises:
        duration_minutes = int(sum((ex.get("duration_min", 0) or 0) for ex in workout.exercises))
    est_burn = int(duration_minutes * 5) if duration_minutes > 0 else 0

    # Today's lifestyle points
    lp = db.query(LifestylePoint).filter(
        LifestylePoint.user_id == user.id,
        LifestylePoint.date == today,
    ).first()

    return DashboardOut(
        user_name=user.name,
        cluster_archetype=user.cluster_archetype,
        bmi=hm.bmi if hm else None,
        diabetes_risk=hm.diabetes_risk_category if hm else None,
        diabetes_risk_score=hm.diabetes_risk_score if hm else None,
        cvd_risk_score=hm.cvd_risk_score if hm else None,
        metrics={
            "diabetes_risk_score": hm.diabetes_risk_score if hm else None,
            "cvd_risk_score": hm.cvd_risk_score if hm else None,
        },
        lifestyle_points=lp.points_total if lp else 0,
        lifestyle_breakdown=lp.points_breakdown if lp else None,
        workout_status=workout.status if workout else "no_plan",
        workout_exercise_count=len(workout.exercises or []) if workout else 0,
        diet_plan_calories=calories_consumed,
        diet_adherence=diet.adherence_score if diet else None,
        calories_consumed=calories_consumed,
        calorie_target=targets.get("calorie_target"),
        water_ml=round(float(water_ml), 1),
        water_target_ml=water_target_ml,
        weight_kg=weight_kg,
        stress_level=round((stress_log.stress_level or 0) * 10, 1) if stress_log else None,
        workout={
            "name": "Today's Workout" if workout else None,
            "exercises_count": len(workout.exercises or []) if workout else 0,
            "duration_minutes": duration_minutes,
            "calories_burn": est_burn,
        } if workout else None,
        diet={
            "meals_logged": len(meals),
            "meals_planned": meals_planned,
            "protein_g": protein_consumed,
            "protein_target": targets.get("protein_target_g"),
            "carbs_g": carbs_consumed,
            "carbs_target": targets.get("carbs_target_g"),
            "fat_g": fat_consumed,
            "fat_target": targets.get("fat_target_g"),
            "fiber_g": fiber_consumed,
            "fiber_target": targets.get("fiber_target_g"),
        },
    )


@router.get("/trends", response_model=DashboardTrends)
def get_trends(
    days: int = 14,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lp_trend = get_lifestyle_points_trend(user.id, db, days)
    cal_trend = get_calorie_trend(user.id, db, days)

    return DashboardTrends(
        lifestyle_points=lp_trend,
        calories=[
            {"date": row["date"], "value": row.get("calories", 0), "total": row.get("calories", 0)}
            for row in cal_trend
        ],
    )
