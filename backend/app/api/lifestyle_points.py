"""Lifestyle Points: today's score, history, force recompute."""
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.progress import LifestylePoint
from app.schemas.lifestyle_points import LifestylePointsOut, LifestylePointsHistory
from app.api.deps import get_current_user
from app.services.lifestyle_points_service import compute_lifestyle_points, force_recompute

router = APIRouter(prefix="/lifestyle-points", tags=["Lifestyle Points"])


@router.get("/today", response_model=LifestylePointsOut)
def today_points(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lp = compute_lifestyle_points(user, db)
    return LifestylePointsOut(
        date=lp.date.isoformat() if isinstance(lp.date, date) else str(lp.date),
        total=lp.points_total,
        breakdown=lp.points_breakdown or {},
    )


@router.post("/recompute", response_model=LifestylePointsOut)
def recompute(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lp = force_recompute(user, db)
    return LifestylePointsOut(
        date=lp.date.isoformat() if isinstance(lp.date, date) else str(lp.date),
        total=lp.points_total,
        breakdown=lp.points_breakdown or {},
    )


@router.get("/history", response_model=list[LifestylePointsHistory])
def points_history(days: int = 30, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    from datetime import timedelta
    cutoff = date.today() - timedelta(days=days)
    entries = db.query(LifestylePoint).filter(
        LifestylePoint.user_id == user.id,
        LifestylePoint.date >= cutoff,
    ).order_by(LifestylePoint.date).all()

    return [
        LifestylePointsHistory(
            date=lp.date.isoformat() if isinstance(lp.date, date) else str(lp.date),
            total=lp.points_total,
            breakdown=lp.points_breakdown or {},
        )
        for lp in entries
    ]
