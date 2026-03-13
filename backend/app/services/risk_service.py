"""Diabetes and CVD risk computation using trained ML models."""
import logging
import numpy as np
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.user import User, Profile, Condition
from app.models.progress import HealthMetric
from app.services.ml_models import ml_models

logger = logging.getLogger(__name__)


def compute_diabetes_risk(user: User, db: Session) -> dict:
    """Run diabetes risk model and persist to HealthMetrics."""
    profile = user.profile
    cond = user.conditions
    if not profile:
        return {"probability": 0, "risk_category": "Low", "method": "no_profile"}

    bmi = (profile.weight_kg or 70) / ((profile.height_cm or 170) / 100) ** 2

    full_features = {
        "Pregnancies": 0,
        "Glucose": 100,
        "BloodPressure": 72,
        "SkinThickness": 20,
        "Insulin": 80,
        "BMI": round(bmi, 1),
        "DiabetesPedigreeFunction": 0.5 if (cond and cond.family_history_diabetes) else 0.2,
        "Age": profile.age or 30,
    }

    # Adjust based on conditions
    if cond:
        if cond.type_2_diabetes or cond.pre_diabetes:
            full_features["Glucose"] = 140
            full_features["Insulin"] = 160
        if cond.obesity:
            full_features["BMI"] = max(full_features["BMI"], 32)

    result = ml_models.diabetes.predict(full_features)

    # Persist
    hm = db.query(HealthMetric).filter(HealthMetric.user_id == user.id).order_by(
        HealthMetric.timestamp.desc()
    ).first()

    if hm is None:
        hm = HealthMetric(user_id=user.id)
        db.add(hm)

    hm.diabetes_risk_score = result["probability"]
    hm.diabetes_risk_category = result["risk_category"]
    hm.bmi = round(bmi, 1)
    hm.weight_kg = profile.weight_kg
    hm.timestamp = datetime.now(timezone.utc)
    db.commit()

    logger.info(f"User {user.id} diabetes risk: {result['risk_category']} ({result['probability']:.3f})")
    return result


def compute_cvd_risk(user: User, db: Session) -> dict:
    """Simple heuristic CVD risk score based on known risk factors."""
    profile = user.profile
    cond = user.conditions
    if not profile:
        return {"score": 0, "category": "Low"}

    score = 0.0
    age = profile.age or 30
    bmi = (profile.weight_kg or 70) / ((profile.height_cm or 170) / 100) ** 2

    if age > 55:
        score += 0.15
    elif age > 45:
        score += 0.10
    if bmi > 30:
        score += 0.15
    elif bmi > 25:
        score += 0.08

    if cond:
        if cond.hypertension:
            score += 0.20
        if cond.high_cholesterol:
            score += 0.15
        if cond.type_2_diabetes:
            score += 0.15
        if cond.family_history_diabetes:
            score += 0.05
        if cond.obesity:
            score += 0.10

    score = min(score, 1.0)
    category = "Low" if score < 0.3 else ("Medium" if score < 0.6 else "High")

    hm = db.query(HealthMetric).filter(HealthMetric.user_id == user.id).order_by(
        HealthMetric.timestamp.desc()
    ).first()
    if hm:
        hm.cvd_risk_score = round(score, 3)
        db.commit()

    return {"score": round(score, 3), "category": category}
