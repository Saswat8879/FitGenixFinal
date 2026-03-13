"""Admin endpoints: user list, DB seed, stats."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from app.database import get_db
from app.models.user import User
from app.models.plan import Exercise, Food
from app.models.progress import LifestylePoint
from app.api.deps import get_admin_user

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
def list_users(skip: int = 0, limit: int = 50,
               admin: User = Depends(get_admin_user),
               db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "is_active": u.is_active,
            "is_mock": u.is_mock,
            "cluster_archetype": u.cluster_archetype,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.get("/stats")
def platform_stats(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    total_users = db.query(sa_func.count(User.id)).scalar() or 0
    active_users = db.query(sa_func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0
    total_exercises = db.query(sa_func.count(Exercise.id)).scalar() or 0
    total_foods = db.query(sa_func.count(Food.id)).scalar() or 0
    avg_points = db.query(sa_func.avg(LifestylePoint.points_total)).scalar() or 0

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_exercises": total_exercises,
        "total_foods": total_foods,
        "avg_lifestyle_points": round(avg_points, 1),
    }


@router.post("/seed-catalog")
def seed_catalog(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Seed exercise and food catalogs from ML processed data."""
    from app.config import settings
    import pandas as pd

    seeded = {"exercises": 0, "foods": 0}

    # Exercises
    ex_path = settings.ml_data_dir / "exercises_clean.csv"
    if ex_path.exists() and db.query(sa_func.count(Exercise.id)).scalar() == 0:
        df = pd.read_csv(ex_path)
        for _, row in df.iterrows():
            ex = Exercise(
                name=row.get("Title", row.get("name", "Unknown")),
                muscle_group=row.get("BodyPart", row.get("muscle_group", "")),
                equipment=row.get("Equipment", row.get("equipment", "")),
                difficulty=row.get("Level", row.get("difficulty", "")),
                body_region=row.get("body_region", ""),
            )
            db.add(ex)
        db.commit()
        seeded["exercises"] = len(df)

    # Foods
    food_path = settings.ml_data_dir / "foods_clean.csv"
    if food_path.exists() and db.query(sa_func.count(Food.id)).scalar() == 0:
        df = pd.read_csv(food_path)
        for _, row in df.iterrows():
            food = Food(
                name=row.get("name", row.get("food_name", "Unknown")),
                calories=row.get("calories", row.get("energy_kcal", 0)),
                protein=row.get("protein", row.get("protein_g", 0)),
                carbs=row.get("carbs", row.get("carbohydrate_g", 0)),
                fat=row.get("fat", row.get("fat_g", 0)),
                fiber=row.get("fiber", row.get("fiber_g", 0)),
                source="seed",
            )
            db.add(food)
        db.commit()
        seeded["foods"] = len(df)

    return {"message": "Catalog seeded", **seeded}
