"""Lifestyle check-ins: stress, sleep, mood, posture, tips."""
from datetime import datetime, timezone, date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.lifestyle import LifestyleLog
from app.schemas.lifestyle import (
    StressOut, LifestyleCheckin, LifestyleCheckinOut, TipsOut, PostureOut,
)
from app.api.deps import get_current_user
from app.services.ml_models import ml_models
from app.services.lifestyle_points_service import force_recompute
from app.utils.timing_utils import ist_start_of_day, ist_end_of_day

router = APIRouter(prefix="/lifestyle", tags=["Lifestyle"])


@router.post("/stress-check", response_model=StressOut)
def stress_check(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Run stress detection model and return result with interventions."""
    import random
    # Build features from recent data (in prod: actual sensor data)
    features = {
        "hr_mean": random.uniform(60, 100),
        "hr_std": random.uniform(3, 15),
        "steps_last_1h": random.randint(0, 500),
        "time_since_activity_min": random.uniform(10, 120),
        "sleep_hours": random.uniform(5, 9),
    }
    result = ml_models.stress.predict(features)

    interventions = []
    if result.get("is_stressed"):
        interventions = ["deep_breathing_5min", "short_walk_10min", "listen_to_calm_music"]

    # Save to lifestyle log
    log = LifestyleLog(
        user_id=user.id,
        stress_level=result.get("probability", 0.3),
        stress_raw=result.get("probability", 0.3),
        is_stressed=result.get("is_stressed", False),
        stress_interventions=interventions,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log)
    db.commit()
    force_recompute(user, db)

    return StressOut(
        stress_level=result.get("probability", 0.3),
        is_stressed=result.get("is_stressed", False),
        interventions=interventions,
        method=result.get("method", "ml"),
    )


@router.post("/checkin", response_model=LifestyleCheckinOut)
def lifestyle_checkin(body: LifestyleCheckin, user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """Submit a daily lifestyle check-in (sleep, mood, hydration, etc.)."""
    log = LifestyleLog(
        user_id=user.id,
        sleep_hours=body.sleep_hours,
        sleep_quality=body.sleep_quality,
        mood=body.mood,
        hydration_ml=body.hydration_ml,
        posture_alert=body.posture_alert,
        sedentary_minutes=body.sedentary_minutes,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    force_recompute(user, db)

    return LifestyleCheckinOut(
        id=log.id,
        sleep_hours=log.sleep_hours,
        sleep_quality=log.sleep_quality,
        mood=log.mood,
        hydration_ml=log.hydration_ml,
        message="Check-in recorded",
    )


@router.get("/tips", response_model=TipsOut)
def get_tips(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate personalized tips based on recent lifestyle data."""
    today = date.today()
    start, end = ist_start_of_day(today), ist_end_of_day(today)

    latest = db.query(LifestyleLog).filter(
        LifestyleLog.user_id == user.id,
    ).order_by(LifestyleLog.timestamp.desc()).first()

    tips = []
    if latest:
        if latest.sleep_hours and latest.sleep_hours < 7:
            tips.append("Try to get 7-9 hours of sleep. Consider a bedtime routine.")
        if latest.mood and latest.mood <= 2:
            tips.append("Your mood seems low. A short walk or stretching can help.")
        if latest.is_stressed:
            tips.append("Stress detected! Try deep breathing (4-7-8 method) for 3 cycles.")
        if latest.sedentary_minutes and latest.sedentary_minutes > 360:
            tips.append("You've been sedentary for a while. Take a 5-min break every hour.")
        if latest.posture_alert:
            tips.append("Remember to check your posture — shoulders back, screen at eye level.")

    if not tips:
        tips = ["Great job today! Keep maintaining your healthy habits.",
                "Stay hydrated — aim for water intake spread across the day."]

    return TipsOut(tips=tips)


@router.get("/posture", response_model=PostureOut)
def posture_check(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Simple posture alert based on work style and sedentary time."""
    profile = user.profile
    desk_worker = profile and profile.work_style and profile.work_style.value in ("desk_job", "remote")

    latest = db.query(LifestyleLog).filter(
        LifestyleLog.user_id == user.id,
    ).order_by(LifestyleLog.timestamp.desc()).first()

    sedentary = latest.sedentary_minutes if latest and latest.sedentary_minutes else 0
    alert = desk_worker and sedentary > 60

    return PostureOut(
        alert=alert,
        sedentary_minutes=sedentary,
        message="Time for a posture break!" if alert else "Posture looks good.",
    )
