"""
FitGenix ML — Inference: Meal Planning
Loads food database and plan meals using ILP solver + health scoring.
"""
import sys, os
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    DATASET_DIR, PROCESSED_DIR, DISEASE_CONSTRAINTS,
)
from utils import logger
from models.food_recommender import FoodScorer, MealPlanner, UserTasteProfile


NONVEG_KW = ["chicken", "mutton", "lamb", "fish", "prawn", "shrimp", "beef", "pork", "meat", "keema", "kebab"]
EGG_KW = ["egg", "eggs", "anda", "omelet", "omelette", "bhurji"]
DAIRY_KW = ["milk", "curd", "paneer", "cheese", "butter", "ghee", "cream", "lassi", "yogurt", "dahi", "whey"]

EXCLUDE_KW = [
    "masala", "powder", "spice blend", "sauce", "chutney", "pickle", "achaar", "achar", "murabba", "jam", "jelly",
    "candy", "preserves", "icing", "frosting", "dressing", "tadka", "baghar", "premix", "squash", "sharbat",
    "tea", "coffee", "cooler", "juice", "mayonnaise",
]

BREAKFAST_KW = ["idli", "dosa", "poha", "upma", "porridge", "daliya", "chilla", "cheela", "omelette", "omelet", "sandwich", "pancake", "puttu", "thepla", "appam"]
LUNCH_DINNER_KW = ["dal", "curry", "paneer", "chicken", "fish", "soup", "khichdi", "khichri", "sabzi", "manchurian", "lababdar", "do pyaza", "stew", "salad", "raita", "kebab"]
SNACK_KW = ["chaat", "dhokla", "khakhra", "biscuit", "cookie", "pakora", "vada", "chips", "roll", "murukku", "namkeen", "sev"]


def _norm(v) -> str:
    return str(v or "").strip().lower()


def _contains_any(text: str, words: list[str]) -> bool:
    return any(w in text for w in words)


def _diet_category(name: str) -> str:
    t = _norm(name)
    if _contains_any(t, NONVEG_KW):
        return "non_vegetarian"
    if _contains_any(t, EGG_KW):
        return "eggetarian"
    if _contains_any(t, DAIRY_KW):
        return "vegetarian"
    return "vegan"


def _is_meal_candidate(name: str) -> bool:
    return not _contains_any(_norm(name), EXCLUDE_KW)


def _meal_slots(name: str) -> list[str]:
    t = _norm(name)
    slots = []
    if _contains_any(t, BREAKFAST_KW):
        slots.append("breakfast")
    if _contains_any(t, LUNCH_DINNER_KW):
        slots.extend(["lunch", "dinner"])
    if _contains_any(t, SNACK_KW):
        slots.append("snack")
    if not slots:
        slots = ["lunch"]
    return list(dict.fromkeys(slots))


def _primary_meal_type(name: str, slots: list[str]) -> str:
    if "breakfast" in slots:
        return "breakfast"
    if "snack" in slots and "lunch" not in slots and "dinner" not in slots:
        return "snack"
    if "lunch" in slots and "dinner" in slots:
        # Deterministic split to keep candidates in both lunch and dinner buckets.
        return "lunch" if (sum(ord(c) for c in _norm(name)) % 2 == 0) else "dinner"
    if "lunch" in slots:
        return "lunch"
    if "dinner" in slots:
        return "dinner"
    if "snack" in slots:
        return "snack"
    return "lunch"


class MealPlanPredictor:
    """Production inference wrapper for food recommendation + meal planning."""

    def __init__(self):
        self.food_df = None
        self.food_embeddings = None
        self.scorer = FoodScorer(health_weight=0.6)
        self.planner = MealPlanner()
        self._loaded = False

    def _load_indian_food_df(self) -> pd.DataFrame:
        csv_path = DATASET_DIR / "Indian_Food_Nutrition_Processed.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Indian food CSV not found: {csv_path}")

        df = pd.read_csv(csv_path)
        df = df.rename(columns={
            "Dish Name": "name",
            "Calories (kcal)": "calories",
            "Carbohydrates (g)": "carbs_g",
            "Protein (g)": "protein_g",
            "Fats (g)": "fat_g",
            "Free Sugar (g)": "sugar_g",
            "Fibre (g)": "fiber_g",
            "Sodium (mg)": "sodium_mg",
        })

        for col in ["calories", "carbs_g", "protein_g", "fat_g", "sugar_g", "fiber_g", "sodium_mg"]:
            if col not in df.columns:
                df[col] = 0.0
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        df["name"] = df["name"].astype(str).str.strip()
        df = df[df["name"].str.len() > 2].copy()
        df = df[df["name"].apply(_is_meal_candidate)].copy()

        # Keep practical meal-level foods.
        df = df[(df["calories"] >= 40) & (df["calories"] <= 650)].copy()
        df = df[df["sodium_mg"] <= 1800].copy()
        df = df[df["sugar_g"] <= 45].copy()
        df = df.drop_duplicates(subset=["name"], keep="first")

        df["diet_category"] = df["name"].apply(_diet_category)
        df["meal_slots"] = df["name"].apply(_meal_slots)
        df["meal_type"] = df.apply(lambda r: _primary_meal_type(r["name"], r["meal_slots"]), axis=1)

        df["vegetarian"] = df["diet_category"].isin(["vegetarian", "vegan"]).astype(int)
        df["vegan"] = (df["diet_category"] == "vegan").astype(int)
        df["low_sodium"] = (df["sodium_mg"] <= 140).astype(int)
        df["diabetic_friendly"] = ((df["sugar_g"] <= 8) & (df["fiber_g"] >= 2)).astype(int)
        df["heart_healthy"] = ((df["sodium_mg"] <= 300) & (df["fat_g"] <= 12)).astype(int)

        # Build stable ids used across API responses.
        df = df.reset_index(drop=True)
        df["food_id"] = df.index + 1
        return df

    @staticmethod
    def _build_food_embeddings(df: pd.DataFrame) -> np.ndarray:
        feat_cols = ["calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g", "sodium_mg"]
        arr = df[feat_cols].astype(float).values
        mean = arr.mean(axis=0, keepdims=True)
        std = arr.std(axis=0, keepdims=True)
        std[std < 1e-6] = 1.0
        z = (arr - mean) / std
        norms = np.linalg.norm(z, axis=1, keepdims=True)
        norms[norms < 1e-6] = 1.0
        return (z / norms).astype(np.float32)

    def load(self):
        """Load preprocessed Indian food catalog and build embeddings."""
        try:
            self.food_df = self._load_indian_food_df()
            self.food_embeddings = self._build_food_embeddings(self.food_df)
            logger.info(f"MealPlanPredictor loaded from Indian CSV. {len(self.food_df)} foods.")
        except Exception as e:
            # Safe fallback keeps app available if CSV preprocessing fails.
            logger.warning(f"Falling back to processed foods due to: {e}")
            self.food_df = pd.read_csv(PROCESSED_DIR / "foods_clean.csv")
            self.food_embeddings = np.load(PROCESSED_DIR / "food_embeddings.npy")
            logger.info(f"MealPlanPredictor fallback loaded. {len(self.food_df)} foods.")
        self._loaded = True

    def plan_day(self, user_profile: dict, taste_profile: UserTasteProfile = None,
                 calorie_target: float = 2000) -> dict:
        """
        Generate a full-day meal plan.

        user_profile: {
            conditions: list[str],       # e.g., ["type2_diabetes"]
            dietary_prefs: list[str],    # e.g., ["vegetarian"]
            dislikes: list[str],         # food names to exclude
            calorie_target: float,
        }

        Returns: {
            meals: {breakfast: [...], lunch: [...], dinner: [...], snack: [...]},
            totals: {calories, protein_g, carbs_g, ...},
            constraint_satisfaction: bool,
        }
        """
        if not self._loaded:
            self.load()

        calorie_target = user_profile.get("calorie_target", calorie_target)
        conditions = user_profile.get("conditions", [])
        dietary_prefs = set(user_profile.get("dietary_prefs", []))
        dislikes = set(user_profile.get("dislikes", []))

        condition_map = {
            "type_2_diabetes": "type2_diabetes",
            "pre_diabetes": "type2_diabetes",
            "hypertension": "hypertension",
            "obesity": "obesity",
            "fatty_liver": "fatty_liver",
        }

        # Build constraint set from conditions
        constraints = {
            "calories_target": calorie_target,
            "min_protein_g": 55,
            "min_fiber_g": 22,
            "max_sodium_mg": 2300,
            "max_sugar_g": 50,
        }
        for cond in conditions:
            mapped = condition_map.get(cond)
            if mapped in DISEASE_CONSTRAINTS:
                constraints.update(DISEASE_CONSTRAINTS[mapped])
        constraints["calories_target"] = calorie_target + constraints.get("calorie_adjustment", 0)

        # Filter food catalog
        candidates = self.food_df.copy()

        # Diet filters
        if "vegan" in dietary_prefs:
            candidates = candidates[candidates["diet_category"] == "vegan"]
        elif "vegetarian" in dietary_prefs:
            candidates = candidates[candidates["diet_category"].isin(["vegetarian", "vegan"])]
        elif "eggetarian" in dietary_prefs:
            candidates = candidates[candidates["diet_category"].isin(["eggetarian", "vegetarian", "vegan"])]
        # non_vegetarian keeps all categories by design.

        # Exclude dislikes
        if dislikes and "name" in candidates.columns:
            dislikes_l = {d.lower() for d in dislikes}
            candidates = candidates[~candidates["name"].str.lower().apply(
                lambda n: any(d in n for d in dislikes_l)
            )]

        if len(candidates) < 10:
            logger.warning("Very few foods after filtering. Relaxing constraints.")
            candidates = self.food_df.copy()

        candidates = candidates.reset_index(drop=True)

        # Score each candidate
        user_taste_embed = np.zeros(self.food_embeddings.shape[1], dtype=np.float32)
        if taste_profile is not None and getattr(taste_profile, "embedding", None) is not None:
            e = np.array(taste_profile.embedding, dtype=np.float32)
            if e.shape[0] == self.food_embeddings.shape[1]:
                user_taste_embed = e

        daily_budget = {
            "calories": constraints["calories_target"],
            "sodium_mg": constraints.get("max_sodium_mg", 2300),
            "sugar_g": constraints.get("max_sugar_g", 50),
        }

        scored_foods = []
        for idx in range(min(len(candidates), 350)):  # Cap for speed
            row = candidates.iloc[idx]
            food_dict = row.to_dict()
            food_embed = self.food_embeddings[idx % len(self.food_embeddings)]

            score = self.scorer.combined_score(
                food=food_dict,
                food_embedding=food_embed,
                user_constraints=constraints,
                user_taste_embedding=user_taste_embed,
                daily_budget_remaining=daily_budget,
            )
            scored_foods.append({
                "food_id": int(row.get("food_id", idx + 1)),
                "name": str(row.get("name", f"food_{idx}")),
                "calories": float(row.get("calories", 200)),
                "protein_g": float(row.get("protein_g", 10)),
                "carbs_g": float(row.get("carbs_g", 30)),
                "fat_g": float(row.get("fat_g", 10)),
                "fiber_g": float(row.get("fiber_g", 3)),
                "sugar_g": float(row.get("sugar_g", 5)),
                "sodium_mg": float(row.get("sodium_mg", 200)),
                "meal_type": str(row.get("meal_type", "lunch")),
                "diabetic_friendly": int(row.get("diabetic_friendly", 0)),
                "heart_healthy": int(row.get("heart_healthy", 0)),
                "low_sodium": int(row.get("low_sodium", 0)),
                "score": score,
            })

        # Run ILP planner
        scored_df = pd.DataFrame(scored_foods)
        food_scores_arr = scored_df["score"].values
        plan = self.planner.plan_day(
            candidate_foods=scored_df,
            food_scores=food_scores_arr,
            user_constraints=constraints,
            calorie_target=constraints["calories_target"],
        )

        # Compute totals from plan_day result
        totals = plan.get("totals", {})
        meals = plan.get("meals", {})
        n_foods = totals.get("n_items", sum(len(v) for v in meals.values()))

        # Check constraint satisfaction
        satisfied = True
        if "max_sugar_g" in constraints and totals.get("sugar_g", 0) > constraints["max_sugar_g"]:
            satisfied = False
        if "max_sodium_mg" in constraints and totals.get("sodium_mg", 0) > constraints["max_sodium_mg"]:
            satisfied = False

        return {
            "meals": meals,
            "totals": totals,
            "constraint_satisfaction": satisfied,
            "n_foods": n_foods,
            "calorie_target": constraints["calories_target"],
        }


if __name__ == "__main__":
    planner = MealPlanPredictor()
    planner.load()

    result = planner.plan_day({
        "conditions": ["type2_diabetes"],
        "dietary_prefs": ["vegetarian"],
        "dislikes": [],
        "calorie_target": 1800,
    })
    print(f"Plan: {result['n_foods']} foods, {result['totals']['calories']} cal")
    for mt, foods in result["meals"].items():
        print(f"  {mt}: {[f['name'] for f in foods]}")
