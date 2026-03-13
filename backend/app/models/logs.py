import enum
from sqlalchemy import (
    Column, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, func,
)
from app.database import Base


class SimulationTypeEnum(str, enum.Enum):
    full_day = "full_day"
    stress_spike = "stress_spike"
    workout_session = "workout_session"
    meal_log = "meal_log"
    weight_gain = "weight_gain"
    weight_loss = "weight_loss"


class MealLog(Base):
    __tablename__ = "meal_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    food_id = Column(Integer, ForeignKey("foods.id"), nullable=True)
    food_name = Column(String(255))
    meal_slot = Column(String(20))  # breakfast/lunch/dinner/snack/other
    portion_g = Column(Float, default=100)
    calories_logged = Column(Float, default=0)
    protein_logged = Column(Float, default=0)
    carbs_logged = Column(Float, default=0)
    fat_logged = Column(Float, default=0)
    fiber_logged = Column(Float, default=0)
    sodium_logged = Column(Float, default=0)
    sugar_logged = Column(Float, default=0)
    saturated_fat_logged = Column(Float, default=0)
    source = Column(String(30), default="manual_search")  # from_plan/manual_search/custom/mock
    notes = Column(String(500), nullable=True)


class WaterLog(Base):
    __tablename__ = "water_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    amount_ml = Column(Float, nullable=False)
    source = Column(String(20), default="manual")


class MockSimulationLog(Base):
    __tablename__ = "mock_simulation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    timestamp = Column(DateTime, server_default=func.now())
    simulation_type = Column(Enum(SimulationTypeEnum), nullable=False)
    input_payload = Column(JSON)
    processed_output = Column(JSON)
    triggered_by = Column(String(100))
