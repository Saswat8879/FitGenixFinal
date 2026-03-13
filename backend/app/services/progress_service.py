"""Progress tracking: weight logs, goal progress, trends."""
import logging
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from app.models.user import User
from app.models.progress import HealthMetric, WeightLog, LifestylePoint
from app.models.logs import MealLog

logger = logging.getLogger(__name__)


def log_weight(user: User, weight_kg: float, notes: str, db: Session) -> WeightLog:
    """Log a weight entry and recompute BMI + health metric."""
    profile = user.profile
    height_m = (profile.height_cm or 170) / 100.0
    bmi = round(weight_kg / (height_m ** 2), 1)

    wl = WeightLog(
        user_id=user.id,
        weight_kg=weight_kg,
        bmi=bmi,
        notes=notes,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(wl)

    # Update profile weight
    if profile:
        profile.weight_kg = weight_kg
    # Update latest health metric
    hm = db.query(HealthMetric).filter(HealthMetric.user_id == user.id).order_by(
        HealthMetric.timestamp.desc()
    ).first()
    if hm:
        hm.weight_kg = weight_kg
        hm.bmi = bmi

    db.commit()
    db.refresh(wl)
    return wl


def get_weight_history(user_id: int, db: Session, days: int = 90) -> list[dict]:
    """Return weight log entries for the last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    logs = db.query(WeightLog).filter(
        WeightLog.user_id == user_id,
        WeightLog.timestamp >= cutoff,
    ).order_by(WeightLog.timestamp).all()

    return [
        {"date": wl.timestamp.date().isoformat(), "weight_kg": wl.weight_kg, "bmi": wl.bmi}
        for wl in logs
    ]


def get_goal_progress(user: User, db: Session) -> dict:
    """Compute percentage progress toward the user's primary goal."""
    profile = user.profile
    if not profile or not profile.goal:
        return {"goal": "none", "percent": 0, "detail": "No goal set"}

    goal = profile.goal.value
    current_weight = profile.weight_kg or 70

    if goal == "lose_weight":
        # Assume target is BMI 24 for now
        height_m = (profile.height_cm or 170) / 100
        target_weight = 24 * (height_m ** 2)
        first_log = db.query(WeightLog).filter(
            WeightLog.user_id == user.id
        ).order_by(WeightLog.timestamp).first()
        start_weight = first_log.weight_kg if first_log else current_weight + 5
        total_to_lose = max(start_weight - target_weight, 1)
        lost = max(start_weight - current_weight, 0)
        pct = min(100, round(lost / total_to_lose * 100, 1))
        return {"goal": goal, "percent": pct, "start_weight": start_weight,
                "current_weight": current_weight, "target_weight": round(target_weight, 1)}

    elif goal == "gain_muscle":
        height_m = (profile.height_cm or 170) / 100
        target_weight = 25 * (height_m ** 2)
        first_log = db.query(WeightLog).filter(
            WeightLog.user_id == user.id
        ).order_by(WeightLog.timestamp).first()
        start_weight = first_log.weight_kg if first_log else current_weight - 3
        total_to_gain = max(target_weight - start_weight, 1)
        gained = max(current_weight - start_weight, 0)
        pct = min(100, round(gained / total_to_gain * 100, 1))
        return {"goal": goal, "percent": pct, "current_weight": current_weight,
                "target_weight": round(target_weight, 1)}

    elif goal == "manage_condition":
        hm = db.query(HealthMetric).filter(HealthMetric.user_id == user.id).order_by(
            HealthMetric.timestamp.desc()
        ).first()
        risk = hm.diabetes_risk_score if hm else 0.5
        # Lower risk = more progress
        pct = round((1 - risk) * 100, 1)
        return {"goal": goal, "percent": pct, "risk_score": risk}

    else:
        # Generic: use lifestyle points average as progress
        recent_points = db.query(sa_func.avg(LifestylePoint.points_total)).filter(
            LifestylePoint.user_id == user.id,
            LifestylePoint.date >= date.today() - timedelta(days=7),
        ).scalar() or 0
        pct = min(100, round(recent_points / 1.05, 1))  # out of 105
        return {"goal": goal, "percent": pct, "avg_points": round(recent_points, 1)}


def get_lifestyle_points_trend(user_id: int, db: Session, days: int = 30) -> list[dict]:
    """Daily lifestyle points for the past N days."""
    cutoff = date.today() - timedelta(days=days)
    points = db.query(LifestylePoint).filter(
        LifestylePoint.user_id == user_id,
        LifestylePoint.date >= cutoff,
    ).order_by(LifestylePoint.date).all()

    return [
        {"date": lp.date.isoformat(), "total": lp.points_total, "breakdown": lp.points_breakdown}
        for lp in points
    ]


def get_platform_average(db: Session) -> dict:
    """Return platform-wide averages for display."""
    avg_points = db.query(sa_func.avg(LifestylePoint.points_total)).filter(
        LifestylePoint.date >= date.today() - timedelta(days=7),
    ).scalar() or 0

    total_users = db.query(sa_func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0

    return {"avg_lifestyle_points": round(avg_points, 1), "active_users": total_users}


def get_calorie_trend(user_id: int, db: Session, days: int = 14) -> list[dict]:
    """Daily calorie totals for trending."""
    from app.utils.timing_utils import ist_start_of_day, ist_end_of_day
    result = []
    for i in range(days):
        d = date.today() - timedelta(days=i)
        start, end = ist_start_of_day(d), ist_end_of_day(d)
        total = db.query(sa_func.sum(MealLog.calories_logged)).filter(
            MealLog.user_id == user_id,
            MealLog.timestamp.between(start, end),
        ).scalar() or 0
        result.append({"date": d.isoformat(), "calories": round(total, 1)})
    result.reverse()
    return result
