"""Indian recipe suggestions from curated CSV with diet-type preprocessing."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import logging
import pandas as pd

logger = logging.getLogger(__name__)

_DF: pd.DataFrame | None = None


def _dataset_path() -> Path:
    return Path(__file__).resolve().parents[3] / "datasets" / "Indian_Food_Nutrition_Processed.csv"


def _norm_text(v: Any) -> str:
    return str(v or "").strip().lower()


def _contains_any(text: str, words: list[str]) -> bool:
    return any(w in text for w in words)


_NONVEG_KW = [
    "chicken", "mutton", "lamb", "fish", "prawn", "shrimp", "beef", "pork", "meat", "keema", "kebab",
]
_EGG_KW = ["egg", "eggs", "anda", "omelet", "omelette", "bhurji"]
_DAIRY_KW = ["milk", "curd", "paneer", "cheese", "butter", "ghee", "cream", "lassi", "yogurt", "dahi", "whey"]

_EXCLUDE_KW = [
    "masala", "powder", "spice blend", "sauce", "chutney", "pickle", "achaar", "achar", "murabba",
    "jam", "jelly", "candy", "preserves", "icing", "frosting", "dressing", "tadka", "baghar", "premix",
    "squash", "sharbat", "tea", "coffee", "cooler", "juice", "mayonnaise",
]

_BREAKFAST_KW = [
    "idli", "dosa", "poha", "upma", "porridge", "daliya", "chilla", "cheela", "omelette", "omelet",
    "sandwich", "pancake", "khichdi", "khichri", "puttu", "thepla", "appam",
]
_LUNCH_DINNER_KW = [
    "dal", "curry", "paneer", "chicken", "fish", "soup", "khichdi", "khichri", "sabzi", "manchurian",
    "lababdar", "do pyaza", "stew", "salad", "raita", "kebab",
]
_SNACK_KW = [
    "chaat", "dhokla", "khakhra", "biscuit", "cookie", "pakora", "vada", "chips", "roll", "murukku",
    "namkeen", "sev",
]


def _compute_category(name: str) -> str:
    t = _norm_text(name)
    if _contains_any(t, _NONVEG_KW):
        return "non_vegetarian"
    if _contains_any(t, _EGG_KW):
        return "eggetarian"
    if _contains_any(t, _DAIRY_KW):
        return "vegetarian"
    return "vegan"


def _preferred_slots(name: str) -> list[str]:
    t = _norm_text(name)
    slots: list[str] = []

    if _contains_any(t, _BREAKFAST_KW):
        slots.append("breakfast")
    if _contains_any(t, _SNACK_KW):
        slots.append("snack")
    if _contains_any(t, _LUNCH_DINNER_KW):
        slots.extend(["lunch", "dinner"])

    if not slots:
        slots = ["lunch", "dinner"]

    # De-duplicate preserving order.
    return list(dict.fromkeys(slots))


def _is_meal_candidate(name: str) -> bool:
    t = _norm_text(name)
    return not _contains_any(t, _EXCLUDE_KW)


def _load_df() -> pd.DataFrame:
    global _DF
    if _DF is not None:
        return _DF

    path = _dataset_path()
    if not path.exists():
        logger.warning("Indian food CSV not found at %s", path)
        _DF = pd.DataFrame()
        return _DF

    df = pd.read_csv(path)
    rename_map = {
        "Dish Name": "name",
        "Calories (kcal)": "calories",
        "Carbohydrates (g)": "carbs_g",
        "Protein (g)": "protein_g",
        "Fats (g)": "fat_g",
        "Free Sugar (g)": "sugar_g",
        "Fibre (g)": "fiber_g",
        "Sodium (mg)": "sodium_mg",
    }
    df = df.rename(columns=rename_map)

    # Keep only the columns we rely on and coerce numerics.
    for col in ["calories", "carbs_g", "protein_g", "fat_g", "sugar_g", "fiber_g", "sodium_mg"]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["name"] = df["name"].astype(str).str.strip()
    df = df[df["name"].str.len() > 2].copy()

    # Keep practical meal candidates and remove condiments/powders/pickles, etc.
    df = df[df["name"].apply(_is_meal_candidate)].copy()

    # Guardrails for realistic per-meal nutrition.
    df = df[(df["calories"] >= 40) & (df["calories"] <= 650)].copy()
    df = df[df["sodium_mg"] <= 1800].copy()
    df = df[df["sugar_g"] <= 45].copy()

    # Deduplicate on dish name.
    df = df.drop_duplicates(subset=["name"], keep="first")

    df["diet_category"] = df["name"].apply(_compute_category)
    df["meal_slots"] = df["name"].apply(_preferred_slots)

    # Heuristic health score for ranking options.
    df["health_score"] = (
        (df["protein_g"] * 2.3)
        + (df["fiber_g"] * 2.2)
        - (df["sugar_g"] * 1.4)
        - (df["sodium_mg"] / 450.0)
        - (df["fat_g"] * 0.5)
    )

    _DF = df
    logger.info("Loaded Indian food dataset with %d rows", len(df))
    return _DF


def _diet_filter(df: pd.DataFrame, diet_type: str | None) -> pd.DataFrame:
    dt = _norm_text(diet_type or "")
    if dt == "vegan":
        return df[df["diet_category"] == "vegan"]
    if dt == "vegetarian":
        return df[df["diet_category"].isin(["vegetarian", "vegan"])]
    if dt == "eggetarian":
        return df[df["diet_category"].isin(["eggetarian", "vegetarian", "vegan"])]
    return df


def _slot_count(slot: str) -> int:
    if slot in ("lunch", "dinner"):
        return 2
    if slot == "breakfast":
        return 2
    return 1


def _slot_ratio(slot: str) -> float:
    return {
        "breakfast": 0.25,
        "lunch": 0.35,
        "dinner": 0.30,
        "snack": 0.10,
    }.get(slot, 0.20)


def _slot_bounds(slot: str) -> tuple[float, float]:
    if slot == "snack":
        return 60, 320
    if slot == "breakfast":
        return 120, 500
    return 180, 650


def recommend_indian_meals(
    diet_type: str | None,
    calorie_target: float,
    slots: tuple[str, ...] = ("breakfast", "lunch", "dinner", "snack"),
) -> dict[str, list[dict[str, Any]]]:
    """Return Indian recipe suggestions for requested meal slots."""
    df = _load_df()
    if df.empty:
        return {}

    cand = _diet_filter(df, diet_type)
    if cand.empty:
        cand = df

    out: dict[str, list[dict[str, Any]]] = {}
    used_names: set[str] = set()

    for slot in slots:
        slot_df = cand[cand["meal_slots"].apply(lambda xs: slot in xs)]
        if slot_df.empty:
            slot_df = cand

        # Avoid repeating dishes across slots.
        if used_names:
            slot_df = slot_df[~slot_df["name"].isin(used_names)]
        if slot_df.empty:
            slot_df = cand

        slot_target = max(calorie_target * _slot_ratio(slot), 120)
        min_c, max_c = _slot_bounds(slot)
        slot_df = slot_df[(slot_df["calories"] >= min_c) & (slot_df["calories"] <= max_c)]
        if slot_df.empty:
            slot_df = cand

        # Prefer recipes near slot calorie budget and with better health score.
        scored = slot_df.copy()
        scored["calorie_fit"] = (scored["calories"] - slot_target).abs() / max(slot_target, 1)
        scored["rank_score"] = scored["health_score"] - (scored["calorie_fit"] * 3.2)
        scored = scored.sort_values("rank_score", ascending=False)

        picks = scored.head(_slot_count(slot)).to_dict("records")
        out[slot] = [
            {
                "food_id": None,
                "name": p["name"],
                "portion_g": 100,
                "calories": float(p.get("calories", 0.0)),
                "protein_g": float(p.get("protein_g", 0.0)),
                "carbs_g": float(p.get("carbs_g", 0.0)),
                "fat_g": float(p.get("fat_g", 0.0)),
                "fiber_g": float(p.get("fiber_g", 0.0)),
                "sodium_mg": float(p.get("sodium_mg", 0.0)),
                "sugar_g": float(p.get("sugar_g", 0.0)),
                "source": "indian_recipe",
            }
            for p in picks
        ]
        used_names.update(p["name"] for p in picks)

    return out
