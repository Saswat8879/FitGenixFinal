from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, func
from app.database import Base


class Leaderboard(Base):
    __tablename__ = "leaderboard"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    weekly_steps = Column(Integer, default=0)
    weekly_workouts_completed = Column(Integer, default=0)
    weekly_streak = Column(Integer, default=0)
    total_points = Column(Float, default=0)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_flagged = Column(Boolean, default=False)
