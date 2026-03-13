import enum
from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, JSON, String, Text, func,
)
from sqlalchemy.orm import relationship
from app.database import Base


class GoalEnum(str, enum.Enum):
    lose_weight = "lose_weight"
    gain_muscle = "gain_muscle"
    maintain = "maintain"
    improve_fitness = "improve_fitness"
    manage_condition = "manage_condition"


class DietTypeEnum(str, enum.Enum):
    vegetarian = "vegetarian"
    vegan = "vegan"
    eggetarian = "eggetarian"
    non_vegetarian = "non_vegetarian"
    pescatarian = "pescatarian"
    keto = "keto"


class CoachingStyleEnum(str, enum.Enum):
    gentle = "gentle"
    moderate = "moderate"
    intense = "intense"


class ActivityLevelEnum(str, enum.Enum):
    sedentary = "sedentary"
    lightly_active = "lightly_active"
    moderately_active = "moderately_active"
    very_active = "very_active"
    extra_active = "extra_active"


class WorkStyleEnum(str, enum.Enum):
    desk_job = "desk_job"
    field_work = "field_work"
    hybrid = "hybrid"
    remote = "remote"
    student = "student"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    last_active = Column(DateTime, server_default=func.now(), onupdate=func.now())
    embedding = Column(JSON, nullable=True)
    cluster_id = Column(Integer, nullable=True)
    cluster_archetype = Column(String(100), nullable=True)
    is_admin = Column(Boolean, default=False)
    is_mock = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True)

    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    conditions = relationship("Condition", back_populates="user", uselist=False, cascade="all, delete-orphan")
    oauth_tokens = relationship("FitOAuthToken", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    age = Column(Integer)
    sex = Column(String(10))
    height_cm = Column(Float)
    weight_kg = Column(Float)
    goal = Column(Enum(GoalEnum))
    diet_type = Column(Enum(DietTypeEnum))
    equipment = Column(JSON, default=list)
    time_available_min = Column(Integer, default=30)
    coaching_style = Column(Enum(CoachingStyleEnum), default=CoachingStyleEnum.moderate)
    country = Column(String(100))
    cuisine_preference = Column(String(100))
    activity_level = Column(Enum(ActivityLevelEnum), default=ActivityLevelEnum.sedentary)
    work_style = Column(Enum(WorkStyleEnum))
    preferred_notifications = Column(Boolean, default=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="profile")


class Condition(Base):
    __tablename__ = "conditions"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    type_2_diabetes = Column(Boolean, default=False)
    pre_diabetes = Column(Boolean, default=False)
    hypertension = Column(Boolean, default=False)
    high_cholesterol = Column(Boolean, default=False)
    fatty_liver = Column(Boolean, default=False)
    obesity = Column(Boolean, default=False)
    asthma_copd = Column(Boolean, default=False)
    back_pain = Column(Boolean, default=False)
    knee_pain = Column(Boolean, default=False)
    shoulder_pain = Column(Boolean, default=False)
    family_history_diabetes = Column(Boolean, default=False)
    on_medication = Column(Boolean, default=False)
    doctor_supervised = Column(Boolean, default=False)

    user = relationship("User", back_populates="conditions")


class FitOAuthToken(Base):
    __tablename__ = "fit_oauth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    expires_at = Column(DateTime)

    user = relationship("User", back_populates="oauth_tokens")
