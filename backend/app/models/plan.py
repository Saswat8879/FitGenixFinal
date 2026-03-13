from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, JSON, String, func,
)
from app.database import Base


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    muscle_group = Column(String(100))
    secondary_muscles = Column(JSON, default=list)
    equipment = Column(String(100))
    difficulty = Column(Integer)  # 1-5
    impact_level = Column(String(20))
    instructions = Column(String(2000))
    contraindications = Column(JSON, default=list)
    body_region = Column(String(100))
    met_value = Column(Float, default=5.0)


class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    date = Column(DateTime, index=True)
    exercises = Column(JSON)  # [{exercise_id, sets, reps, duration_min}]
    status = Column(String(20), default="planned")  # planned / completed / skipped
    completed_at = Column(DateTime, nullable=True)
    feedback_json = Column(JSON, nullable=True)
    source = Column(String(20), default="ml")  # ml / mock


class Food(Base):
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    cuisine = Column(String(100))
    meal_type = Column(String(20))
    calories = Column(Float, default=0)
    protein = Column(Float, default=0)
    carbs = Column(Float, default=0)
    fat = Column(Float, default=0)
    fiber = Column(Float, default=0)
    sodium = Column(Float, default=0)
    sugar = Column(Float, default=0)
    saturated_fat = Column(Float, default=0)
    tags = Column(JSON, default=list)
    embedding_index = Column(Integer, nullable=True)
    source = Column(String(30), default="usda")  # usda/openfoodfacts/indian_db/calorieninjas/user_custom


class DietPlan(Base):
    __tablename__ = "diet_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    date = Column(DateTime, index=True)
    meals_json = Column(JSON)  # {breakfast: [...], lunch: [...], dinner: [...], snack: [...]}
    total_calories = Column(Float, default=0)
    total_protein = Column(Float, default=0)
    total_carbs = Column(Float, default=0)
    total_fat = Column(Float, default=0)
    total_sodium = Column(Float, default=0)
    adherence_score = Column(Float, default=0)
    source = Column(String(20), default="ml")
