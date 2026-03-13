"""Workout and diet plan generation using ML models."""
import logging
import random
import numpy as np
from datetime import datetime, timezone, date
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.plan import Workout, DietPlan
from app.services.ml_models import ml_models
from app.services.indian_food_service import recommend_indian_meals
from app.utils.timing_utils import ist_start_of_day, ist_end_of_day

logger = logging.getLogger(__name__)

EXPLORATION_RATE = 0.15
DIET_PLAN_GENERATOR_VERSION = "indian_csv_v1"


def _user_exercise_profile(user: User) -> dict:
    cond = user.conditions
    profile = user.profile
    conditions = []
    if cond:
        for attr in ["type_2_diabetes", "hypertension", "obesity", "asthma_copd",
                      "back_pain", "knee_pain", "shoulder_pain"]:
            if getattr(cond, attr, False):
                conditions.append(attr)

    equipment = profile.equipment if profile and profile.equipment else ["None"]
    fitness_level = {
        "sedentary": 1, "lightly_active": 2, "moderately_active": 3,
        "very_active": 4, "extra_active": 5,
    }.get(profile.activity_level.value if profile and profile.activity_level else "sedentary", 2)

    return {
        "conditions": conditions,
        "fitness_level": fitness_level,
        "equipment_available": equipment,
        "exercises_per_workout": max(4, min(8, (profile.time_available_min or 30) // 5)),
        "today_focus": None,
    }


def get_diet_targets(user: User) -> dict:
    """Compute BMR/TDEE and daily macro targets using Mifflin-St Jeor."""
    profile = user.profile
    if not profile:
        return {
            "bmr": 1600.0,
            "tdee": 1920.0,
            "calorie_target": 1900,
            "protein_target_g": 100.0,
            "carbs_target_g": 220.0,
            "fat_target_g": 63.0,
            "fiber_target_g": 30.0,
        }

    weight_kg = float(profile.weight_kg or 70.0)
    height_cm = float(profile.height_cm or 170.0)
    age = float(profile.age or 30.0)
    sex = str(profile.sex or "").strip().lower()

    sex_offset = -78.0
    if sex.startswith("m"):
        sex_offset = 5.0
    elif sex.startswith("f"):
        sex_offset = -161.0

    bmr = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age) + sex_offset

    activity_mult = {
        "sedentary": 1.20,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "extra_active": 1.90,
    }
    level = profile.activity_level.value if profile.activity_level else "sedentary"
    tdee = bmr * activity_mult.get(level, 1.20)

    goal_factor = 1.0
    protein_per_kg = 1.0
    if profile.goal:
        g = profile.goal.value
        if g == "lose_weight":
            goal_factor = 0.82
            protein_per_kg = 1.3
        elif g == "gain_muscle":
            goal_factor = 1.10
            protein_per_kg = 1.6
        elif g == "manage_condition":
            goal_factor = 0.90
            protein_per_kg = 1.2
        elif g == "improve_fitness":
            goal_factor = 0.95
            protein_per_kg = 1.1

    calorie_target = int(round(tdee * goal_factor))
    calorie_target = max(1200, min(4200, calorie_target))

    protein_target_g = max(50.0, round(weight_kg * protein_per_kg, 1))
    fat_target_g = max(35.0, round((calorie_target * 0.27) / 9.0, 1))
    carbs_target_g = max(
        80.0,
        round((calorie_target - ((protein_target_g * 4.0) + (fat_target_g * 9.0))) / 4.0, 1),
    )
    fiber_target_g = round(min(max((calorie_target / 1000.0) * 14.0, 20.0), 45.0), 1)

    return {
        "bmr": round(bmr, 1),
        "tdee": round(tdee, 1),
        "calorie_target": calorie_target,
        "protein_target_g": protein_target_g,
        "carbs_target_g": carbs_target_g,
        "fat_target_g": fat_target_g,
        "fiber_target_g": fiber_target_g,
    }


def _user_diet_profile(user: User) -> dict:
    cond = user.conditions
    profile = user.profile
    conditions = []
    if cond:
        for attr in ["type_2_diabetes", "pre_diabetes", "hypertension",
                      "high_cholesterol", "fatty_liver", "obesity"]:
            if getattr(cond, attr, False):
                conditions.append(attr)

    dietary_prefs = []
    if profile and profile.diet_type:
        dietary_prefs.append(profile.diet_type.value)

    targets = get_diet_targets(user)

    return {
        "conditions": conditions,
        "dietary_prefs": dietary_prefs,
        "dislikes": [],
        **targets,
    }


def generate_workout(user: User, db: Session, target_date: date | None = None) -> Workout:
    """Generate and save a daily workout plan."""
    target_date = target_date or date.today()
    user_profile = _user_exercise_profile(user)
    embedding = np.array(user.embedding or [0] * 16, dtype=np.float32)

    exercises = ml_models.exercise.recommend(user_profile, embedding, top_k=user_profile["exercises_per_workout"])

    # Safety filters can occasionally return an empty list; keep UX functional with a conservative fallback.
    if not exercises:
        logger.warning("No exercises recommended for user %s, using fallback set", user.id)
        exercises = [
            {"exercise_id": -1, "name": "Brisk Walking", "body_part": "Full Body", "type": "Cardio", "score": 0.3},
            {"exercise_id": -2, "name": "Bodyweight Squats", "body_part": "Legs", "type": "Strength", "score": 0.3},
            {"exercise_id": -3, "name": "Wall Push-Ups", "body_part": "Chest", "type": "Strength", "score": 0.3},
            {"exercise_id": -4, "name": "Plank Hold", "body_part": "Core", "type": "Strength", "score": 0.3},
        ]

    # Exploration injection
    if random.random() < EXPLORATION_RATE and len(exercises) > 2:
        idx = random.randint(0, len(exercises) - 1)
        exercises[idx]["exploration"] = True

    # Build exercise payload
    exercise_data = []
    for ex in exercises:
        sets = 3 if user_profile["fitness_level"] >= 3 else 2
        reps = 12 if ex.get("type") == "Strength" else 1
        duration = 10 if ex.get("type") == "Cardio" else 0
        exercise_data.append({
            "exercise_id": ex.get("exercise_id"),
            "name": ex.get("name", "Unknown"),
            "body_part": ex.get("body_part", "Other"),
            "type": ex.get("type", "Strength"),
            "sets": sets,
            "reps": reps,
            "duration_min": duration,
            "score": ex.get("score", 0),
            "exploration": ex.get("exploration", False),
        })

    start, end = ist_start_of_day(target_date), ist_end_of_day(target_date)
    workout = db.query(Workout).filter(
        Workout.user_id == user.id,
        Workout.date.between(start, end),
    ).order_by(Workout.id.desc()).first()

    if workout:
        workout.exercises = exercise_data
        workout.status = "planned"
        workout.completed_at = None
        workout.feedback_json = None
        workout.source = "ml"
        workout.date = datetime.combine(target_date, datetime.min.time())
    else:
        workout = Workout(
            user_id=user.id,
            date=datetime.combine(target_date, datetime.min.time()),
            exercises=exercise_data,
            status="planned",
            source="ml",
        )
        db.add(workout)

    db.commit()
    db.refresh(workout)
    logger.info(f"Generated workout for user {user.id}: {len(exercise_data)} exercises")
    return workout


def generate_diet_plan(user: User, db: Session, target_date: date | None = None) -> DietPlan:
    """Generate and save a daily diet plan."""
    target_date = target_date or date.today()
    diet_profile = _user_diet_profile(user)

    result = ml_models.meal.plan_day(diet_profile)

    meals = result.get("meals", {})
    totals = result.get("totals", {})

    # Replace meal slots with curated Indian recipe suggestions by diet type.
    profile = user.profile
    diet_type = profile.diet_type.value if profile and profile.diet_type else None
    indian_meals = recommend_indian_meals(
        diet_type=diet_type,
        calorie_target=diet_profile.get("calorie_target", 2000),
        slots=("breakfast", "lunch", "dinner", "snack"),
    )
    for slot in ("breakfast", "lunch", "dinner", "snack"):
        if indian_meals.get(slot):
            meals[slot] = indian_meals[slot]

    meals["_meta"] = {
        "generator_version": DIET_PLAN_GENERATOR_VERSION,
        "generator": "indian_csv_preprocessed",
        "calorie_target": diet_profile.get("calorie_target"),
        "protein_target_g": diet_profile.get("protein_target_g"),
        "carbs_target_g": diet_profile.get("carbs_target_g"),
        "fat_target_g": diet_profile.get("fat_target_g"),
        "fiber_target_g": diet_profile.get("fiber_target_g"),
        "bmr": diet_profile.get("bmr"),
        "tdee": diet_profile.get("tdee"),
    }

    # Recompute totals from finalized meal map to keep persistence accurate.
    def _sum(field: str) -> float:
        s = 0.0
        for items in meals.values():
            if not isinstance(items, list):
                continue
            for it in items:
                s += float(it.get(field, 0.0) or 0.0)
        return s

    totals = {
        "calories": _sum("calories"),
        "protein_g": _sum("protein_g"),
        "carbs_g": _sum("carbs_g"),
        "fat_g": _sum("fat_g"),
        "fiber_g": _sum("fiber_g"),
        "sodium_mg": _sum("sodium_mg"),
    }

    start, end = ist_start_of_day(target_date), ist_end_of_day(target_date)
    plan = db.query(DietPlan).filter(
        DietPlan.user_id == user.id,
        DietPlan.date.between(start, end),
    ).order_by(DietPlan.id.desc()).first()

    if plan:
        plan.date = datetime.combine(target_date, datetime.min.time())
        plan.meals_json = meals
        plan.total_calories = totals.get("calories", 0)
        plan.total_protein = totals.get("protein_g", 0)
        plan.total_carbs = totals.get("carbs_g", 0)
        plan.total_fat = totals.get("fat_g", 0)
        plan.total_sodium = totals.get("sodium_mg", 0)
        plan.adherence_score = 0
        plan.source = "ml"
    else:
        plan = DietPlan(
            user_id=user.id,
            date=datetime.combine(target_date, datetime.min.time()),
            meals_json=meals,
            total_calories=totals.get("calories", 0),
            total_protein=totals.get("protein_g", 0),
            total_carbs=totals.get("carbs_g", 0),
            total_fat=totals.get("fat_g", 0),
            total_sodium=totals.get("sodium_mg", 0),
            adherence_score=0,
            source="ml",
        )
        db.add(plan)

    db.commit()
    db.refresh(plan)
    logger.info(f"Generated diet plan for user {user.id}: {result.get('n_foods', 0)} foods, "
                f"{totals.get('calories', 0):.0f} cal")
    return plan
