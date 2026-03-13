"""Health metrics and risk scores."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.progress import HealthMetric
from app.schemas.health import HealthMetricOut, RiskOut
from app.api.deps import get_current_user
from app.services.risk_service import compute_diabetes_risk, compute_cvd_risk

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/metrics", response_model=HealthMetricOut)
def get_metrics(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    hm = db.query(HealthMetric).filter(
        HealthMetric.user_id == user.id
    ).order_by(HealthMetric.timestamp.desc()).first()

    if not hm:
        return HealthMetricOut(
            bmi=None, weight_kg=None,
            diabetes_risk_score=None, diabetes_risk_category=None,
            cvd_risk_score=None, stress_level=None,
            resting_hr=None, avg_daily_steps=None,
            avg_active_minutes=None, avg_sleep_hours=None,
        )

    return HealthMetricOut(
        bmi=hm.bmi,
        weight_kg=hm.weight_kg,
        diabetes_risk_score=hm.diabetes_risk_score,
        diabetes_risk_category=hm.diabetes_risk_category,
        cvd_risk_score=hm.cvd_risk_score,
        stress_level=hm.stress_level,
        resting_hr=hm.resting_hr,
        avg_daily_steps=hm.avg_daily_steps,
        avg_active_minutes=hm.avg_active_minutes,
        avg_sleep_hours=hm.avg_sleep_hours,
    )


@router.post("/risk/diabetes", response_model=RiskOut)
def run_diabetes_risk(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = compute_diabetes_risk(user, db)
    return RiskOut(
        risk_type="diabetes",
        score=result["probability"],
        category=result["risk_category"],
        method=result.get("method", "ensemble"),
    )


@router.post("/risk/cvd", response_model=RiskOut)
def run_cvd_risk(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = compute_cvd_risk(user, db)
    return RiskOut(
        risk_type="cvd",
        score=result["score"],
        category=result["category"],
        method="heuristic",
    )


@router.post("/risk/refresh")
def refresh_all_risks(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Re-run all risk computations."""
    d = compute_diabetes_risk(user, db)
    c = compute_cvd_risk(user, db)
    return {
        "diabetes": {"score": d["probability"], "category": d["risk_category"]},
        "cvd": {"score": c["score"], "category": c["category"]},
    }
