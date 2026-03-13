"""Meal and water logging endpoints."""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from app.database import get_db
from app.models.user import User
from app.models.logs import MealLog, WaterLog
from app.schemas.logs import (
    MealFromPlan, MealSearch, MealSearchResult, MealConfirm,
    MealCustom, MealLogOut, WaterLogCreate, WaterLogOut, WaterTodayOut,
)
from app.api.deps import get_current_user
from app.services.food_log_service import (
    log_meal_from_plan, log_meal_from_search, log_meal_custom,
    search_foods_in_db, get_today_meals,
)
from app.services.lifestyle_points_service import force_recompute
from app.services.calorieninjas_service import search_food
from app.utils.timing_utils import ist_start_of_day, ist_end_of_day
from datetime import datetime, timezone

router = APIRouter(prefix="/logs", tags=["Logs"])


# ── Meal Logging ──

@router.post("/meal/from-plan", response_model=MealLogOut)
def meal_from_plan(body: MealFromPlan, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    ml = log_meal_from_plan(
        user_id=user.id,
        food_id=body.food_id,
        meal_slot=body.meal_slot,
        portion_g=body.portion_g,
        db=db,
        food_name=body.food_name,
        calories=body.calories,
        protein_g=body.protein_g,
        carbs_g=body.carbs_g,
        fat_g=body.fat_g,
        fiber_g=body.fiber_g,
        sodium_mg=body.sodium_mg,
        sugar_g=body.sugar_g,
        saturated_fat_g=body.saturated_fat_g,
    )
    force_recompute(user, db)
    return _meal_out(ml)


@router.post("/meal/search", response_model=list[MealSearchResult])
async def meal_search(body: MealSearch, user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    # Try local DB first
    local = search_foods_in_db(body.query, db, limit=5)
    # Then CalorieNinjas
    external = await search_food(body.query)
    results = []
    for item in local:
        results.append(MealSearchResult(
            name=item["name"], source="local_db",
            calories=item.get("calories", 0), protein_g=item.get("protein", 0),
            carbs_g=item.get("carbs", 0), fat_g=item.get("fat", 0),
            fiber_g=item.get("fiber", 0),
            food_id=item.get("id"),
        ))
    for item in external:
        results.append(MealSearchResult(
            name=item["name"], source="calorieninjas",
            calories=item.get("calories", 0), protein_g=item.get("protein_g", 0),
            carbs_g=item.get("carbohydrates_total_g", 0), fat_g=item.get("fat_total_g", 0),
            fiber_g=item.get("fiber_g", 0),
        ))
    return results


@router.post("/meal/confirm", response_model=MealLogOut)
def meal_confirm(body: MealConfirm, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    nutrition = {
        "name": body.name,
        "calories": body.calories,
        "protein_g": body.protein_g,
        "carbohydrates_total_g": body.carbs_g,
        "fat_total_g": body.fat_g,
        "fiber_g": body.fiber_g,
        "sodium_mg": body.sodium_mg,
        "sugar_g": body.sugar_g,
        "fat_saturated_g": body.saturated_fat_g,
    }
    ml = log_meal_from_search(user.id, nutrition, body.meal_slot, body.portion_g, db)
    force_recompute(user, db)
    return _meal_out(ml)


@router.post("/meal/custom", response_model=MealLogOut)
def meal_custom(body: MealCustom, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    ml = log_meal_custom(
        user_id=user.id, food_name=body.food_name, meal_slot=body.meal_slot,
        portion_g=body.portion_g, calories=body.calories, protein=body.protein,
        carbs=body.carbs, fat=body.fat, fiber=body.fiber, sodium=body.sodium,
        sugar=body.sugar, saturated_fat=body.saturated_fat, db=db,
    )
    force_recompute(user, db)
    return _meal_out(ml)


@router.get("/meals/today", response_model=list[MealLogOut])
def meals_today(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    meals = get_today_meals(user.id, db)
    return [_meal_out(m) for m in meals]


# ── Water Logging ──

@router.post("/water", response_model=WaterLogOut)
def log_water(body: WaterLogCreate, user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    wl = WaterLog(
        user_id=user.id,
        amount_ml=body.amount_ml,
        source=body.source or "manual",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(wl)
    db.commit()
    db.refresh(wl)
    force_recompute(user, db)
    return WaterLogOut(id=wl.id, amount_ml=wl.amount_ml, timestamp=wl.timestamp, source=wl.source)


@router.get("/water/today", response_model=WaterTodayOut)
def water_today(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    start, end = ist_start_of_day(today), ist_end_of_day(today)
    total = db.query(sa_func.sum(WaterLog.amount_ml)).filter(
        WaterLog.user_id == user.id,
        WaterLog.timestamp.between(start, end),
    ).scalar() or 0
    count = db.query(sa_func.count(WaterLog.id)).filter(
        WaterLog.user_id == user.id,
        WaterLog.timestamp.between(start, end),
    ).scalar() or 0
    profile = user.profile
    target = int((profile.weight_kg or 70) * 35) if profile else 2500
    return WaterTodayOut(total_ml=total, target_ml=target, log_count=count)


def _meal_out(m: MealLog) -> MealLogOut:
    return MealLogOut(
        id=m.id,
        food_name=m.food_name,
        meal_slot=m.meal_slot,
        portion_g=m.portion_g,
        calories=m.calories_logged,
        protein=m.protein_logged,
        carbs=m.carbs_logged,
        fat=m.fat_logged,
        fiber=m.fiber_logged,
        timestamp=m.timestamp,
        source=m.source,
    )
