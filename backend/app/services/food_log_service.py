"""Food logging: from plan, manual search, custom entry. Adherence tracking."""
import logging
from datetime import datetime, timezone, date
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.plan import Food, DietPlan
from app.models.logs import MealLog

logger = logging.getLogger(__name__)


def log_meal_from_plan(user_id: int, food_id: int | None, meal_slot: str,
                       portion_g: float, db: Session,
                       food_name: str | None = None,
                       calories: float | None = None,
                       protein_g: float | None = None,
                       carbs_g: float | None = None,
                       fat_g: float | None = None,
                       fiber_g: float | None = None,
                       sodium_mg: float | None = None,
                       sugar_g: float | None = None,
                       saturated_fat_g: float | None = None) -> MealLog:
    """Log a meal by picking a food from the current diet plan (or food DB)."""
    food = db.query(Food).get(food_id) if food_id is not None else None

    if not food:
        # Fallback for plan items sourced from non-DB catalogs (e.g., curated CSV recipes).
        scale = portion_g / 100.0
        log = MealLog(
            user_id=user_id,
            food_name=food_name or "Planned meal",
            meal_slot=meal_slot,
            portion_g=portion_g,
            calories_logged=round((calories or 0) * scale, 1),
            protein_logged=round((protein_g or 0) * scale, 1),
            carbs_logged=round((carbs_g or 0) * scale, 1),
            fat_logged=round((fat_g or 0) * scale, 1),
            fiber_logged=round((fiber_g or 0) * scale, 1),
            sodium_logged=round((sodium_mg or 0) * scale, 1),
            sugar_logged=round((sugar_g or 0) * scale, 1),
            saturated_fat_logged=round((saturated_fat_g or 0) * scale, 1),
            source="plan",
            timestamp=datetime.now(timezone.utc),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        _update_adherence(user_id, db)
        return log

    scale = portion_g / 100.0
    log = MealLog(
        user_id=user_id,
        food_id=food.id,
        food_name=food.name,
        meal_slot=meal_slot,
        portion_g=portion_g,
        calories_logged=round((food.calories or 0) * scale, 1),
        protein_logged=round((food.protein or 0) * scale, 1),
        carbs_logged=round((food.carbs or 0) * scale, 1),
        fat_logged=round((food.fat or 0) * scale, 1),
        fiber_logged=round((food.fiber or 0) * scale, 1),
        sodium_logged=round((food.sodium or 0) * scale, 1),
        sugar_logged=round((food.sugar or 0) * scale, 1),
        saturated_fat_logged=round((food.saturated_fat or 0) * scale, 1),
        source="plan",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    _update_adherence(user_id, db)
    return log


def log_meal_from_search(user_id: int, nutrition: dict, meal_slot: str,
                         portion_g: float, db: Session) -> MealLog:
    """Log a meal from CalorieNinjas search result (already resolved nutrition)."""
    log = MealLog(
        user_id=user_id,
        food_name=nutrition.get("name", "Unknown"),
        meal_slot=meal_slot,
        portion_g=portion_g,
        calories_logged=nutrition.get("calories", 0),
        protein_logged=nutrition.get("protein_g", 0),
        carbs_logged=nutrition.get("carbohydrates_total_g", 0),
        fat_logged=nutrition.get("fat_total_g", 0),
        fiber_logged=nutrition.get("fiber_g", 0),
        sodium_logged=nutrition.get("sodium_mg", 0),
        sugar_logged=nutrition.get("sugar_g", 0),
        saturated_fat_logged=nutrition.get("fat_saturated_g", 0),
        source="search",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    _update_adherence(user_id, db)
    return log


def log_meal_custom(user_id: int, food_name: str, meal_slot: str, portion_g: float,
                    calories: float, protein: float, carbs: float, fat: float,
                    fiber: float = 0, sodium: float = 0, sugar: float = 0,
                    saturated_fat: float = 0, db: Session = None) -> MealLog:
    """Log a fully custom meal entry."""
    log = MealLog(
        user_id=user_id,
        food_name=food_name,
        meal_slot=meal_slot,
        portion_g=portion_g,
        calories_logged=calories,
        protein_logged=protein,
        carbs_logged=carbs,
        fat_logged=fat,
        fiber_logged=fiber,
        sodium_logged=sodium,
        sugar_logged=sugar,
        saturated_fat_logged=saturated_fat,
        source="custom",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    _update_adherence(user_id, db)
    return log


def search_foods_in_db(query: str, db: Session, limit: int = 10) -> list[dict]:
    """Search the local food catalog by name."""
    foods = db.query(Food).filter(
        Food.name.ilike(f"%{query}%")
    ).limit(limit).all()

    return [
        {
            "id": f.id,
            "name": f.name,
            "calories": f.calories,
            "protein": f.protein,
            "carbs": f.carbs,
            "fat": f.fat,
            "fiber": f.fiber,
            "source": f.source or "local_db",
        }
        for f in foods
    ]


def _update_adherence(user_id: int, db: Session):
    """Update today's DietPlan adherence score based on logged meals."""
    from app.utils.timing_utils import ist_start_of_day, ist_end_of_day
    today = date.today()
    start, end = ist_start_of_day(today), ist_end_of_day(today)

    plan = db.query(DietPlan).filter(
        DietPlan.user_id == user_id,
        DietPlan.date.between(start, end),
    ).first()
    if not plan or not plan.total_calories:
        return

    meals = db.query(MealLog).filter(
        MealLog.user_id == user_id,
        MealLog.timestamp.between(start, end),
    ).all()

    total_logged = sum(m.calories_logged or 0 for m in meals)
    target = plan.total_calories
    deviation = abs(total_logged - target) / target if target else 1
    adherence = max(0, 100 * (1 - deviation))
    plan.adherence_score = round(adherence, 1)
    db.commit()


def get_today_meals(user_id: int, db: Session, day: date | None = None) -> list[MealLog]:
    from app.utils.timing_utils import ist_start_of_day, ist_end_of_day
    day = day or date.today()
    start, end = ist_start_of_day(day), ist_end_of_day(day)
    return db.query(MealLog).filter(
        MealLog.user_id == user_id,
        MealLog.timestamp.between(start, end),
    ).order_by(MealLog.timestamp).all()
