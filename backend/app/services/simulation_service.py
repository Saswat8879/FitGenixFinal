"""Simulation / demo endpoints for generating and testing data."""
import logging
import random
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.activity import Activity
from app.models.plan import Workout, DietPlan
from app.models.logs import MealLog, WaterLog, MockSimulationLog
from app.models.lifestyle import LifestyleLog
from app.models.progress import WeightLog
from app.services.ml_models import ml_models

logger = logging.getLogger(__name__)


def simulate_full_day(user: User, db: Session) -> dict:
    """Simulate a complete day of activities, meals, hydration, sleep, stress."""
    today = datetime.now(timezone.utc)
    results = {}

    # 1. Morning water (6:30 AM)
    wl = WaterLog(user_id=user.id, amount_ml=300, source="mock",
                  timestamp=today.replace(hour=1, minute=0))  # ~6:30 IST
    db.add(wl)

    # 2. Steps activity
    steps = random.randint(4000, 12000)
    act = Activity(user_id=user.id, timestamp=today.replace(hour=3), type="steps",
                   data_json={"steps": steps, "active_minutes": steps // 100}, source="mock")
    db.add(act)
    results["steps"] = steps

    # 3. Meals (breakfast, lunch, snack, dinner)
    meals = [
        ("breakfast", 350, 20, 45, 12, 5, 3, 1, today.replace(hour=2, minute=30)),
        ("lunch", 550, 30, 60, 18, 8, 600, 5, today.replace(hour=7, minute=0)),
        ("snack", 200, 10, 25, 8, 3, 2, 1, today.replace(hour=10, minute=0)),
        ("dinner", 500, 28, 55, 16, 6, 500, 4, today.replace(hour=13, minute=30)),
    ]
    for slot, cal, prot, carb, fat, fiber, sodium, sugar, ts in meals:
        ml = MealLog(
            user_id=user.id, food_name=f"Mock {slot}", meal_slot=slot,
            portion_g=random.randint(200, 400),
            calories_logged=cal + random.randint(-50, 50),
            protein_logged=prot, carbs_logged=carb, fat_logged=fat,
            fiber_logged=fiber, sodium_logged=sodium, sugar_logged=sugar,
            saturated_fat_logged=random.randint(1, 4),
            source="mock", timestamp=ts,
        )
        db.add(ml)
    results["meals_logged"] = 4

    # 4. Water throughout day
    for h in [5, 8, 11, 14]:
        wl2 = WaterLog(user_id=user.id, amount_ml=random.choice([250, 300, 350]),
                        source="mock", timestamp=today.replace(hour=h))
        db.add(wl2)
    results["water_logs"] = 5

    # 5. Stress check-in
    stress_raw = random.uniform(0.1, 0.8)
    is_stressed = stress_raw > 0.5
    interventions = ["deep_breathing", "walk"] if is_stressed else []
    llog = LifestyleLog(
        user_id=user.id,
        stress_level=stress_raw,
        stress_raw=stress_raw,
        is_stressed=is_stressed,
        stress_interventions=interventions,
        sleep_hours=round(random.uniform(5.5, 9.0), 1),
        sleep_quality=random.randint(2, 5),
        hydration_ml=random.randint(1800, 3000),
        mood=random.randint(2, 5),
        posture_alert=random.choice([True, False]),
        sedentary_minutes=random.randint(120, 480),
        timestamp=today,
    )
    db.add(llog)
    results["stress_level"] = round(stress_raw, 2)
    results["is_stressed"] = is_stressed

    # 6. Workout completion
    from app.services.plan_service import generate_workout
    workout = generate_workout(user, db)
    workout.status = "completed"
    workout.completed_at = today.replace(hour=4)
    results["workout_completed"] = True

    # Log simulation
    sim_log = MockSimulationLog(
        user_id=user.id,
        simulation_type="full_day",
        input_payload={},
        processed_output=results,
        triggered_by="api",
    )
    db.add(sim_log)
    db.commit()

    # Compute lifestyle points
    from app.services.lifestyle_points_service import force_recompute
    lp = force_recompute(user, db)
    results["lifestyle_points"] = lp.points_total

    return results


def simulate_stress_spike(user: User, db: Session) -> dict:
    """Simulate a high-stress event with ML stress detection."""
    raw_features = {
        "hr_mean": random.uniform(80, 120),
        "hr_std": random.uniform(10, 25),
        "steps_last_1h": random.randint(0, 200),
        "time_since_activity_min": random.uniform(0, 60),
        "sleep_hours": random.uniform(4, 7),
    }
    result = ml_models.stress.predict(raw_features)

    now = datetime.now(timezone.utc)
    interventions = ["deep_breathing", "meditation", "walk_5min"] if result.get("is_stressed") else []

    llog = LifestyleLog(
        user_id=user.id,
        stress_level=result.get("probability", 0.7),
        stress_raw=result.get("probability", 0.7),
        is_stressed=result.get("is_stressed", True),
        stress_interventions=interventions,
        timestamp=now,
    )
    db.add(llog)

    sim_log = MockSimulationLog(
        user_id=user.id,
        simulation_type="stress_spike",
        input_payload={"features": raw_features},
        processed_output=result,
        triggered_by="api",
    )
    db.add(sim_log)
    db.commit()

    return {**result, "interventions": interventions}


def simulate_weight_trend(user: User, db: Session, direction: str = "loss",
                          days: int = 30) -> dict:
    """Simulate a weight trend over N days."""
    profile = user.profile
    start_weight = profile.weight_kg or 70
    height_m = (profile.height_cm or 170) / 100

    entries = []
    for i in range(days):
        if direction == "loss":
            delta = -random.uniform(0.05, 0.2)
        else:
            delta = random.uniform(0.05, 0.15)

        w = round(start_weight + delta * (i + 1), 1)
        bmi = round(w / (height_m ** 2), 1)
        ts = datetime.now(timezone.utc) - timedelta(days=days - i)

        wl = WeightLog(user_id=user.id, weight_kg=w, bmi=bmi, notes=f"sim_{direction}",
                       timestamp=ts)
        db.add(wl)
        entries.append({"day": i + 1, "weight": w, "bmi": bmi})

    sim_log = MockSimulationLog(
        user_id=user.id,
        simulation_type=f"weight_{direction}",
        input_payload={"direction": direction, "days": days},
        processed_output={"entries_count": len(entries)},
        triggered_by="api",
    )
    db.add(sim_log)
    db.commit()

    return {"direction": direction, "days": days, "entries": entries}


def simulate_meal_log(user: User, db: Session) -> dict:
    """Simulate a quick meal log with random nutrition."""
    now = datetime.now(timezone.utc)
    slots = ["breakfast", "lunch", "dinner", "snack"]
    slot = random.choice(slots)

    cal = random.randint(200, 700)
    ml = MealLog(
        user_id=user.id, food_name="Simulated Meal", meal_slot=slot,
        portion_g=random.randint(150, 400),
        calories_logged=cal, protein_logged=random.randint(10, 40),
        carbs_logged=random.randint(20, 80), fat_logged=random.randint(5, 25),
        fiber_logged=random.randint(2, 10), sodium_logged=random.randint(100, 800),
        sugar_logged=random.randint(2, 20), saturated_fat_logged=random.randint(1, 8),
        source="mock", timestamp=now,
    )
    db.add(ml)
    db.commit()
    db.refresh(ml)

    return {"id": ml.id, "meal_slot": slot, "calories": cal}


def simulate_workout_complete(user: User, db: Session) -> dict:
    """Simulate generating and instantly completing a workout."""
    from app.services.plan_service import generate_workout

    workout = generate_workout(user, db)
    workout.status = "completed"
    workout.completed_at = datetime.now(timezone.utc)
    workout.feedback_json = {"difficulty": random.choice(["easy", "moderate", "hard"]),
                             "enjoyment": random.randint(3, 5)}
    db.commit()

    return {"workout_id": workout.id, "exercises": len(workout.exercises or []),
            "status": workout.status}


def reset_simulation_data(user_id: int, db: Session) -> dict:
    """Remove all mock/simulation data for a user."""
    deleted = {}
    for model, name in [
        (MealLog, "meal_logs"), (WaterLog, "water_logs"),
        (Activity, "activities"), (LifestyleLog, "lifestyle_logs"),
        (WeightLog, "weight_logs"), (MockSimulationLog, "sim_logs"),
    ]:
        count = db.query(model).filter(
            model.user_id == user_id,
            model.source == "mock" if hasattr(model, "source") else True,
        ).delete(synchronize_session=False)
        deleted[name] = count

    db.commit()
    return deleted
