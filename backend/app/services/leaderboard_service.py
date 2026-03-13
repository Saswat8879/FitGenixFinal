"""Community leaderboard with fraud detection."""
import logging
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from app.models.user import User
from app.models.community import Leaderboard
from app.models.activity import Activity
from app.models.plan import Workout
from app.models.progress import LifestylePoint
from app.utils.fraud_check import should_flag_leaderboard

logger = logging.getLogger(__name__)


def update_leaderboard(user: User, db: Session) -> Leaderboard:
    """Recompute weekly leaderboard stats for a user."""
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())  # Monday
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    # Weekly steps
    steps_total = db.query(sa_func.sum(
        sa_func.json_extract(Activity.data_json, "$.steps")
    )).filter(
        Activity.user_id == user.id,
        Activity.type == "steps",
        Activity.timestamp >= week_start,
    ).scalar() or 0

    # Weekly workouts completed
    workouts_done = db.query(sa_func.count(Workout.id)).filter(
        Workout.user_id == user.id,
        Workout.status == "completed",
        Workout.completed_at >= week_start,
    ).scalar() or 0

    # Streak: consecutive days with lifestyle points > 60
    streak = 0
    for i in range(30):
        d = date.today() - timedelta(days=i)
        lp = db.query(LifestylePoint).filter(
            LifestylePoint.user_id == user.id,
            LifestylePoint.date == d,
        ).first()
        if lp and lp.points_total > 60:
            streak += 1
        else:
            break

    # Total points this week
    total_pts = db.query(sa_func.sum(LifestylePoint.points_total)).filter(
        LifestylePoint.user_id == user.id,
        LifestylePoint.date >= week_start.date(),
    ).scalar() or 0

    # Fraud detection
    flagged = should_flag_leaderboard(
        steps=steps_total,
        workouts=workouts_done,
        water_ml=0,
        calories=0,
    )

    lb = db.query(Leaderboard).filter(Leaderboard.user_id == user.id).first()
    if lb:
        lb.weekly_steps = int(steps_total)
        lb.weekly_workouts_completed = workouts_done
        lb.weekly_streak = streak
        lb.total_points = round(total_pts, 1)
        lb.is_flagged = flagged
        lb.last_updated = now
    else:
        lb = Leaderboard(
            user_id=user.id,
            weekly_steps=int(steps_total),
            weekly_workouts_completed=workouts_done,
            weekly_streak=streak,
            total_points=round(total_pts, 1),
            is_flagged=flagged,
            last_updated=now,
        )
        db.add(lb)

    db.commit()
    db.refresh(lb)
    return lb


def get_leaderboard(db: Session, top_n: int = 20) -> list[dict]:
    """Return top N users by total_points, excluding flagged."""
    entries = db.query(Leaderboard, User.name).join(
        User, User.id == Leaderboard.user_id
    ).filter(
        Leaderboard.is_flagged.is_(False),
    ).order_by(Leaderboard.total_points.desc()).limit(top_n).all()

    return [
        {
            "rank": i + 1,
            "user_id": lb.user_id,
            "name": name,
            "weekly_steps": lb.weekly_steps,
            "workouts_completed": lb.weekly_workouts_completed,
            "streak": lb.weekly_streak,
            "total_points": lb.total_points,
        }
        for i, (lb, name) in enumerate(entries)
    ]


def get_my_rank(user_id: int, db: Session) -> dict:
    """Return the user's current rank and stats."""
    lb = db.query(Leaderboard).filter(Leaderboard.user_id == user_id).first()
    if not lb:
        return {"rank": None, "total_points": 0, "message": "Not on leaderboard yet"}

    # Count how many users have more points (unflagged)
    rank = db.query(sa_func.count(Leaderboard.user_id)).filter(
        Leaderboard.total_points > lb.total_points,
        Leaderboard.is_flagged.is_(False),
    ).scalar() + 1

    return {
        "rank": rank,
        "weekly_steps": lb.weekly_steps,
        "workouts_completed": lb.weekly_workouts_completed,
        "streak": lb.weekly_streak,
        "total_points": lb.total_points,
        "is_flagged": lb.is_flagged,
    }
