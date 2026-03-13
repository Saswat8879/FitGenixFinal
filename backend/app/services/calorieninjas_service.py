"""CalorieNinjas API wrapper for food search/nutrition lookup."""
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.calorieninjas.com/v1/nutrition"


async def search_food(query: str) -> list[dict]:
    """Query CalorieNinjas and return nutrition data for the given food string."""
    api_key = settings.CALORIENINJAS_API_KEY
    if not api_key:
        logger.warning("CalorieNinjas API key not configured, returning empty result")
        return []

    headers = {"X-Api-Key": api_key}
    params = {"query": query}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(BASE_URL, headers=headers, params=params)

    if resp.status_code != 200:
        logger.error(f"CalorieNinjas returned {resp.status_code}: {resp.text[:200]}")
        return []

    data = resp.json()
    items = data.get("items", [])

    results = []
    for item in items:
        results.append({
            "name": item.get("name", ""),
            "calories": item.get("calories", 0),
            "serving_size_g": item.get("serving_size_g", 100),
            "fat_total_g": item.get("fat_total_g", 0),
            "fat_saturated_g": item.get("fat_saturated_g", 0),
            "protein_g": item.get("protein_g", 0),
            "sodium_mg": item.get("sodium_mg", 0),
            "potassium_mg": item.get("potassium_mg", 0),
            "cholesterol_mg": item.get("cholesterol_mg", 0),
            "carbohydrates_total_g": item.get("carbohydrates_total_g", 0),
            "fiber_g": item.get("fiber_g", 0),
            "sugar_g": item.get("sugar_g", 0),
        })

    logger.info(f"CalorieNinjas: '{query}' → {len(results)} items")
    return results
