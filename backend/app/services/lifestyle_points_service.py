"""Lifestyle Points scoring system (WHO/AHA/NSF grounded)."""
import logging
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from app.models.user import User, Profile, Condition
from app.models.plan import DietPlan, Workout
from app.models.logs import MealLog, WaterLog
from app.models.lifestyle import LifestyleLog
from app.models.activity import Activity
from app.models.progress import LifestylePoint
from app.utils.timing_utils import (
    ist_start_of_day, ist_end_of_day, to_ist,
    meal_spacing_ok, post_meal_activity_ok,
    morning_hydration, exercise_in_window,
    sleep_consistency, late_night_meal,
)

logger = logging.getLogger(__name__)

# Debounce: recompute at most every 15 min per user
_last_compute: dict[int, datetime] = {}
DEBOUNCE_SECONDS = 900


def _exercise_score(user: User, db: Session, day: date) -> float:
    start, end = ist_start_of_day(day), ist_end_of_day(day)

    # Active minutes from activities
    activities = db.query(Activity).filter(
        Activity.user_id == user.id,
        Activity.timestamp.between(start, end),
        Activity.type.in_(["workout", "steps"]),
    ).all()

    active_minutes = 0
    is_strength = False
    for a in activities:
        data = a.data_json or {}
        active_minutes += data.get("active_minutes", 0)
        active_minutes += data.get("duration_min", 0)
        if data.get("type") == "Strength" or a.type == "workout":
            is_strength = True

    # Also count completed workouts
    workouts = db.query(Workout).filter(
        Workout.user_id == user.id,
        Workout.date.between(start, end),
        Workout.status == "completed",
    ).all()
    for w in workouts:
        is_strength = True
        for ex in (w.exercises or []):
            active_minutes += ex.get("duration_min", 5)

    # Adjust target for COPD/asthma
    cond = user.conditions
    target = 20 if (cond and cond.asthma_copd) else 30

    base = min(active_minutes / target, 1.0) * 20
    strength_bonus = 2 if is_strength else 0
    return min(base + strength_bonus, 20)


def _diet_score(user: User, db: Session, day: date) -> float:
    start, end = ist_start_of_day(day), ist_end_of_day(day)

    meals = db.query(MealLog).filter(
        MealLog.user_id == user.id,
        MealLog.timestamp.between(start, end),
    ).all()

    if not meals:
        return 0.0

    total_cal = sum(m.calories_logged or 0 for m in meals)
    total_protein = sum(m.protein_logged or 0 for m in meals)
    total_fiber = sum(m.fiber_logged or 0 for m in meals)
    total_sugar = sum(m.sugar_logged or 0 for m in meals)

    # Get calorie target from diet plan
    plan = db.query(DietPlan).filter(
        DietPlan.user_id == user.id,
        DietPlan.date.between(start, end),
    ).first()
    cal_target = plan.total_calories if plan else 2000

    # Calorie adherence (8 pts)
    cal_dev = abs(total_cal - cal_target)
    cal_score = 8 if cal_dev <= 150 else max(0, 8 * (1 - cal_dev / cal_target))

    # Protein target (4 pts) — ~0.8g/kg
    profile = user.profile
    protein_target = (profile.weight_kg or 70) * 0.8
    protein_score = 4 if total_protein >= protein_target else (total_protein / protein_target) * 4

    # Fiber ≥ 25g (4 pts)
    fiber_score = 4 if total_fiber >= 25 else (total_fiber / 25) * 4

    # Sugar within disease limit (4 pts)
    cond = user.conditions
    sugar_limit = 50
    if cond and (cond.type_2_diabetes or cond.pre_diabetes):
        sugar_limit = 25
    sugar_score = 4 if total_sugar <= sugar_limit else 0

    return min(cal_score + protein_score + fiber_score + sugar_score, 20)


def _hydration_score(user: User, db: Session, day: date) -> float:
    start, end = ist_start_of_day(day), ist_end_of_day(day)

    logs = db.query(WaterLog).filter(
        WaterLog.user_id == user.id,
        WaterLog.timestamp.between(start, end),
    ).all()

    total_ml = sum(l.amount_ml for l in logs)
    profile = user.profile
    target_ml = (profile.weight_kg or 70) * 35 if profile else 2500

    base = min(total_ml / target_ml, 1.0) * 20

    # Time distribution bonus
    unique_hours = len(set(to_ist(l.timestamp).hour for l in logs if l.timestamp))
    time_bonus = 2 if unique_hours >= 4 else 0

    return min(base + time_bonus, 20)


def _sleep_score(user: User, db: Session, day: date) -> float:
    start, end = ist_start_of_day(day), ist_end_of_day(day)

    log = db.query(LifestyleLog).filter(
        LifestyleLog.user_id == user.id,
        LifestyleLog.timestamp.between(start, end),
        LifestyleLog.sleep_hours.isnot(None),
    ).order_by(LifestyleLog.timestamp.desc()).first()

    if not log or log.sleep_hours is None:
        return 0.0

    hours = log.sleep_hours
    if 7 <= hours <= 9:
        raw = 20
    elif hours < 6:
        raw = 5
    elif 6 <= hours < 7:
        raw = 12
    elif hours > 9:
        raw = 14
    else:
        raw = 10

    quality = log.sleep_quality or 3
    return min(raw * (quality / 5.0), 20)


def _stress_score(user: User, db: Session, day: date) -> float:
    start, end = ist_start_of_day(day), ist_end_of_day(day)

    log = db.query(LifestyleLog).filter(
        LifestyleLog.user_id == user.id,
        LifestyleLog.timestamp.between(start, end),
        LifestyleLog.stress_level.isnot(None),
    ).order_by(LifestyleLog.timestamp.desc()).first()

    if not log:
        return 10.0  # neutral default

    stress = log.stress_level or 0.3
    base = (1 - stress) * 20

    interventions = log.stress_interventions or []
    intervention_bonus = 4 if (log.is_stressed and len(interventions) > 0) else 0

    return min(base + intervention_bonus, 20)


def _timing_score(user: User, db: Session, day: date) -> float:
    start, end = ist_start_of_day(day), ist_end_of_day(day)
    prev_start = ist_start_of_day(day - timedelta(days=1))

    # Gather timestamps
    meals = db.query(MealLog).filter(
        MealLog.user_id == user.id,
        MealLog.timestamp.between(start, end),
    ).order_by(MealLog.timestamp).all()

    water_logs = db.query(WaterLog).filter(
        WaterLog.user_id == user.id,
        WaterLog.timestamp.between(start, end),
    ).order_by(WaterLog.timestamp).all()

    workouts = db.query(Workout).filter(
        Workout.user_id == user.id,
        Workout.date.between(start, end),
        Workout.status == "completed",
    ).all()

    today_sleep = db.query(LifestyleLog).filter(
        LifestyleLog.user_id == user.id,
        LifestyleLog.timestamp.between(start, end),
        LifestyleLog.sleep_hours.isnot(None),
    ).first()

    yesterday_sleep = db.query(LifestyleLog).filter(
        LifestyleLog.user_id == user.id,
        LifestyleLog.timestamp.between(prev_start, start),
        LifestyleLog.sleep_hours.isnot(None),
    ).first()

    score = 0.0

    # Meal spacing (5 pts)
    major_meals = [m for m in meals if m.meal_slot in ("breakfast", "lunch", "dinner")]
    major_ts = [m.timestamp for m in major_meals if m.timestamp]
    if meal_spacing_ok(major_ts, 3.0) and len(major_ts) >= 2:
        score += 5

    # Post-meal activity gap (3 pts)
    meal_ts = [m.timestamp for m in meals if m.timestamp]
    workout_ts = [w.completed_at or w.date for w in workouts if w.completed_at or w.date]
    if post_meal_activity_ok(meal_ts, workout_ts, 60):
        score += 3

    # Morning hydration (3 pts)
    water_ts = [w.timestamp for w in water_logs if w.timestamp]
    if morning_hydration(water_ts):
        score += 3

    # Exercise timing (3 pts)
    if exercise_in_window(workout_ts):
        score += 3

    # Sleep consistency (3 pts)
    ts1 = today_sleep.timestamp if today_sleep else None
    ts2 = yesterday_sleep.timestamp if yesterday_sleep else None
    if sleep_consistency(ts1, ts2):
        score += 3

    # Late-night eating penalty (-3)
    if late_night_meal(meal_ts):
        score -= 3

    return max(min(score, 20), 0)


def _consistency_bonus(user_id: int, db: Session, day: date) -> float:
    # Look back up to 7 days
    bonus = 0
    streak = 0
    for i in range(1, 8):
        d = day - timedelta(days=i)
        lp = db.query(LifestylePoint).filter(
            LifestylePoint.user_id == user_id,
            LifestylePoint.date == d,
        ).first()
        if lp and lp.points_total > 60:
            streak += 1
        else:
            break

    if streak >= 7:
        bonus = 5
    elif streak >= 3:
        bonus = 2
    return bonus


def compute_lifestyle_points(user: User, db: Session, day: date | None = None) -> LifestylePoint:
    """Compute full daily lifestyle score for a user."""
    day = day or date.today()

    # Debounce check
    now = datetime.now(timezone.utc)
    key = user.id
    if key in _last_compute:
        elapsed = (now - _last_compute[key]).total_seconds()
        if elapsed < DEBOUNCE_SECONDS:
            existing = db.query(LifestylePoint).filter(
                LifestylePoint.user_id == user.id,
                LifestylePoint.date == day,
            ).first()
            if existing:
                return existing
    _last_compute[key] = now

    exercise = _exercise_score(user, db, day)
    diet = _diet_score(user, db, day)
    hydration = _hydration_score(user, db, day)
    sleep = _sleep_score(user, db, day)
    stress = _stress_score(user, db, day)
    timing = _timing_score(user, db, day)
    consistency = _consistency_bonus(user.id, db, day)

    total = min(exercise + diet + hydration + sleep + stress + timing + consistency, 105)

    breakdown = {
        "exercise_score": round(exercise, 1),
        "diet_score": round(diet, 1),
        "hydration_score": round(hydration, 1),
        "sleep_score": round(sleep, 1),
        "stress_score": round(stress, 1),
        "timing_score": round(timing, 1),
        "consistency_bonus": round(consistency, 1),
    }

    lp = db.query(LifestylePoint).filter(
        LifestylePoint.user_id == user.id,
        LifestylePoint.date == day,
    ).first()

    if lp:
        lp.points_total = round(total, 1)
        lp.points_breakdown = breakdown
        lp.computed_at = now
    else:
        lp = LifestylePoint(
            user_id=user.id,
            date=day,
            points_total=round(total, 1),
            points_breakdown=breakdown,
            computed_at=now,
        )
        db.add(lp)

    db.commit()
    db.refresh(lp)
    logger.info(f"User {user.id} lifestyle points for {day}: {total:.1f}")
    return lp


def force_recompute(user: User, db: Session, day: date | None = None) -> LifestylePoint:
    """Force recompute bypassing debounce."""
    _last_compute.pop(user.id, None)
    return compute_lifestyle_points(user, db, day)
