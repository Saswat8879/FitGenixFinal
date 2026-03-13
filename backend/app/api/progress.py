"""Progress: weight tracking, goal progress, trends."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.progress import (
    WeightLogCreate, WeightLogOut, WeightLogResponse,
    GoalProgress, TrendPoint, LifestylePointsTrend, PlatformAverage,
)
from app.api.deps import get_current_user
from app.services.progress_service import (
    log_weight, get_weight_history, get_goal_progress,
    get_lifestyle_points_trend, get_platform_average,
)

router = APIRouter(prefix="/progress", tags=["Progress"])


@router.post("/weight", response_model=WeightLogResponse)
def add_weight(body: WeightLogCreate, user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    wl = log_weight(user, body.weight_kg, body.notes or "", db)
    return WeightLogResponse(
        id=wl.id,
        weight_kg=wl.weight_kg,
        bmi=wl.bmi,
        timestamp=wl.timestamp,
        message="Weight logged",
    )


@router.get("/weight", response_model=list[WeightLogOut])
def weight_history(days: int = 90, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    entries = get_weight_history(user.id, db, days)
    return [WeightLogOut(**e) for e in entries]


@router.get("/goal", response_model=GoalProgress)
def goal_progress(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = get_goal_progress(user, db)
    return GoalProgress(**result)


@router.get("/lifestyle-points", response_model=list[TrendPoint])
def lifestyle_trend(days: int = 30, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    data = get_lifestyle_points_trend(user.id, db, days)
    return [TrendPoint(date=d["date"], value=d["total"]) for d in data]


@router.get("/platform-average", response_model=PlatformAverage)
def platform_avg(db: Session = Depends(get_db)):
    data = get_platform_average(db)
    return PlatformAverage(**data)
