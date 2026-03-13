from sqlalchemy import (
    Column, Date, DateTime, Float, ForeignKey, Integer, JSON, String, func,
)
from app.database import Base


class HealthMetric(Base):
    __tablename__ = "health_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    bmi = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    diabetes_risk_score = Column(Float, nullable=True)
    diabetes_risk_category = Column(String(10), nullable=True)
    cvd_risk_score = Column(Float, nullable=True)
    stress_level = Column(Float, nullable=True)
    resting_hr = Column(Float, nullable=True)
    avg_daily_steps = Column(Float, nullable=True)
    avg_active_minutes = Column(Float, nullable=True)
    avg_sleep_hours = Column(Float, nullable=True)


class WeightLog(Base):
    __tablename__ = "weight_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    weight_kg = Column(Float, nullable=False)
    bmi = Column(Float, nullable=True)
    notes = Column(String(500), nullable=True)


class LifestylePoint(Base):
    __tablename__ = "lifestyle_points"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    date = Column(Date, index=True)
    points_total = Column(Float, default=0)
    points_breakdown = Column(JSON)
    computed_at = Column(DateTime, server_default=func.now())
