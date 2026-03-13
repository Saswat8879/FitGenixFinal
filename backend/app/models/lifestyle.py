from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, func,
)
from app.database import Base


class LifestyleLog(Base):
    __tablename__ = "lifestyle_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    stress_level = Column(Float, nullable=True)      # 0-1 probability
    stress_raw = Column(Float, nullable=True)
    is_stressed = Column(Boolean, default=False)
    stress_interventions = Column(JSON, default=list)
    sleep_hours = Column(Float, nullable=True)
    sleep_quality = Column(Integer, nullable=True)    # 1-5
    hydration_ml = Column(Float, nullable=True)
    mood = Column(Integer, nullable=True)             # 1-5
    posture_alert = Column(Boolean, default=False)
    sedentary_minutes = Column(Integer, default=0)
    source = Column(JSON, default="manual")
