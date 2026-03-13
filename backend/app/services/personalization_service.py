"""Personalization: user embedding, clustering, feature vector construction."""
import logging
import numpy as np
from sqlalchemy.orm import Session
from app.models.user import User, Profile, Condition
from app.models.progress import HealthMetric
from app.services.ml_models import ml_models

logger = logging.getLogger(__name__)

GOAL_MAP = {
    "lose_weight": [1, 0, 0, 0, 0],
    "gain_muscle": [0, 1, 0, 0, 0],
    "maintain": [0, 0, 1, 0, 0],
    "improve_fitness": [0, 0, 0, 1, 0],
    "manage_condition": [0, 0, 0, 0, 1],
}

DIET_MAP = {
    "vegetarian": [1, 0, 0],
    "vegan": [0, 1, 0],
    "keto": [0, 0, 1],
}

ACTIVITY_LEVEL_MAP = {
    "sedentary": 1, "lightly_active": 2, "moderately_active": 3,
    "very_active": 4, "extra_active": 5,
}

EQUIPMENT_MAP = {"None": 0, "Bands": 1, "Dumbbell": 2, "Barbell": 3, "Machine": 4}


def build_user_feature_vector(user: User, db: Session) -> np.ndarray:
    """Build 30-dim feature vector matching ML training schema."""
    profile = user.profile
    cond = user.conditions
    hm = db.query(HealthMetric).filter(HealthMetric.user_id == user.id).order_by(
        HealthMetric.timestamp.desc()
    ).first()

    # Demographic (5)
    age = (profile.age or 30) / 100.0
    sex = 1.0 if (profile.sex or "").lower() in ("male", "m") else 0.0
    bmi = ((profile.weight_kg or 70) / ((profile.height_cm or 170) / 100) ** 2) / 50.0
    num_conditions = 0
    if cond:
        for attr in ["type_2_diabetes", "pre_diabetes", "hypertension", "high_cholesterol",
                      "fatty_liver", "obesity", "asthma_copd", "back_pain", "knee_pain", "shoulder_pain"]:
            if getattr(cond, attr, False):
                num_conditions += 1
    num_conditions /= 10.0
    fitness = ACTIVITY_LEVEL_MAP.get(profile.activity_level.value if profile.activity_level else "sedentary", 1) / 5.0

    # Goal features (10)
    goal_vec = GOAL_MAP.get(profile.goal.value if profile.goal else "maintain", [0, 0, 1, 0, 0])
    diet_vec = DIET_MAP.get(profile.diet_type.value if profile.diet_type else "", [0, 0, 0])
    avail_time = (profile.time_available_min or 30) / 120.0
    equip = len(profile.equipment or []) / 5.0

    # Behavior features (15) — from health metrics or defaults
    if hm:
        avg_steps = (hm.avg_daily_steps or 5000) / 20000.0
        active_min = (hm.avg_active_minutes or 30) / 120.0
        avg_hr = (hm.resting_hr or 72) / 120.0
        sleep_hrs = (hm.avg_sleep_hours or 7) / 12.0
        stress = hm.stress_level or 0.3
    else:
        avg_steps, active_min, avg_hr, sleep_hrs, stress = 0.25, 0.25, 0.6, 0.58, 0.3

    behavior = [
        avg_steps, active_min, avg_hr,
        0.5,       # hr_variability default
        3.0 / 7,   # workout_count_weekly
        0.7,       # workout_completion_rate
        0.5,       # avg_workout_duration
        sleep_hrs,
        0.7,       # sleep_consistency
        0.6,       # diet_adherence_rate
        0.1,       # calorie_deviation_pct
        stress,
        0.2,       # pain_score
        0.6,       # mood_score
        0.5,       # days_since_last_workout normalized
    ]

    features = [age, sex, bmi, num_conditions, fitness] + goal_vec + diet_vec + [avail_time, equip] + behavior
    return np.array(features, dtype=np.float32)


def compute_user_embedding(user: User, db: Session) -> dict:
    """Compute embedding and cluster for a user. Updates User record."""
    features = build_user_feature_vector(user, db)
    result = ml_models.embedding.predict(features)

    user.embedding = result["embedding"] if isinstance(result["embedding"], list) else result["embedding"].tolist()
    user.cluster_id = result["cluster_id"]
    user.cluster_archetype = result.get("archetype", "unknown")
    db.commit()

    logger.info(f"User {user.id} → cluster {user.cluster_id} ({user.cluster_archetype})")
    return result
