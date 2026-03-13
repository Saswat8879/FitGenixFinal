import numpy as np
import pandas as pd
from typing import Optional

try:
    import pulp
except ImportError:
    pulp = None  # Install with: pip install pulp


class FoodScorer:

    def __init__(self, health_weight: float = 0.6):
        self.health_weight = health_weight

    def health_score(self, food: dict, user_constraints: dict,
                     daily_budget_remaining: dict) -> float:

        score = 1.0
        penalties = 0.0

        # Calorie fit: penalize if food is too calorie-dense relative to remaining budget
        cal_remaining = daily_budget_remaining.get("calories", 500)
        if cal_remaining > 0:
            cal_ratio = food.get("calories", 0) / max(cal_remaining, 1)
            if cal_ratio > 0.5:  # Single food > 50% remaining budget
                penalties += 0.2
        else:
            penalties += 0.3  # Over budget

        # Sodium penalty
        max_sodium = user_constraints.get("max_sodium_mg", 2300)
        sodium_remaining = daily_budget_remaining.get("sodium_mg", max_sodium)
        if food.get("sodium_mg", 0) > sodium_remaining * 0.4:
            penalties += 0.15

        # Sugar penalty
        max_sugar = user_constraints.get("max_sugar_g", 50)
        sugar_remaining = daily_budget_remaining.get("sugar_g", max_sugar)
        if food.get("sugar_g", 0) > sugar_remaining * 0.4:
            penalties += 0.15

        # Fiber bonus
        if food.get("fiber_g", 0) > 3:
            score += 0.1

        # Disease-specific bonuses
        if user_constraints.get("diabetic_friendly") and food.get("diabetic_friendly"):
            score += 0.15
        if user_constraints.get("heart_healthy") and food.get("heart_healthy"):
            score += 0.15
        if user_constraints.get("low_sodium") and food.get("low_sodium"):
            score += 0.1

        return max(0.0, min(1.0, score - penalties))

    def preference_score(self, food_embedding: np.ndarray,
                         user_taste_embedding: np.ndarray,
                         cuisine_match: bool = False,
                         past_frequency: float = 0.0) -> float:

        # Cosine similarity
        norm_f = np.linalg.norm(food_embedding)
        norm_u = np.linalg.norm(user_taste_embedding)
        if norm_f < 1e-8 or norm_u < 1e-8:
            sim = 0.0
        else:
            sim = float(np.dot(food_embedding, user_taste_embedding) / (norm_f * norm_u))

        score = (sim + 1) / 2  # Normalize from [-1,1] to [0,1]

        if cuisine_match:
            score += 0.1
        # Slight bonus for foods eaten before (familiarity)
        score += min(past_frequency * 0.05, 0.15)

        return min(1.0, score)

    def combined_score(self, food: dict, food_embedding: np.ndarray,
                       user_constraints: dict, user_taste_embedding: np.ndarray,
                       daily_budget_remaining: dict,
                       cuisine_match: bool = False,
                       past_frequency: float = 0.0) -> float:
        h = self.health_score(food, user_constraints, daily_budget_remaining)
        p = self.preference_score(food_embedding, user_taste_embedding,
                                  cuisine_match, past_frequency)
        return self.health_weight * h + (1 - self.health_weight) * p


class MealPlanner:
    def __init__(self):
        if pulp is None:
            raise ImportError("PuLP is required for meal planning. Install: pip install pulp")

    def plan_day(self, candidate_foods: pd.DataFrame,
                 food_scores: np.ndarray,
                 user_constraints: dict,
                 calorie_target: float,
                 calorie_tolerance: float = 150) -> dict:
        n = len(candidate_foods)
        if n == 0:
            return {"meals": {}, "totals": {}, "status": "no_candidates"}

        # Create ILP problem
        prob = pulp.LpProblem("MealPlan", pulp.LpMaximize)

        # Decision variables: x[i] = 1 if food i is selected
        x = [pulp.LpVariable(f"x_{i}", cat="Binary") for i in range(n)]

        # Objective: maximize total score
        prob += pulp.lpSum(food_scores[i] * x[i] for i in range(n))

        # Calorie constraint
        cals = candidate_foods["calories"].values
        prob += pulp.lpSum(cals[i] * x[i] for i in range(n)) >= calorie_target - calorie_tolerance
        prob += pulp.lpSum(cals[i] * x[i] for i in range(n)) <= calorie_target + calorie_tolerance

        # Protein minimum
        min_protein = user_constraints.get("min_protein_g", 50)
        if "protein_g" in candidate_foods.columns:
            prot = candidate_foods["protein_g"].values
            prob += pulp.lpSum(prot[i] * x[i] for i in range(n)) >= min_protein

        # Sodium maximum
        max_sodium = user_constraints.get("max_sodium_mg", 2300)
        if "sodium_mg" in candidate_foods.columns:
            sod = candidate_foods["sodium_mg"].values
            prob += pulp.lpSum(sod[i] * x[i] for i in range(n)) <= max_sodium

        # Sugar maximum
        max_sugar = user_constraints.get("max_sugar_g", 50)
        if "sugar_g" in candidate_foods.columns:
            sug = candidate_foods["sugar_g"].values
            prob += pulp.lpSum(sug[i] * x[i] for i in range(n)) <= max_sugar

        # Fiber minimum
        min_fiber = user_constraints.get("min_fiber_g", 20)
        if "fiber_g" in candidate_foods.columns:
            fib = candidate_foods["fiber_g"].values
            prob += pulp.lpSum(fib[i] * x[i] for i in range(n)) >= min_fiber

        # Total items: 4-8 foods per day
        prob += pulp.lpSum(x[i] for i in range(n)) >= 4
        prob += pulp.lpSum(x[i] for i in range(n)) <= 8

        # At least 1 food per meal type (if available)
        for mt in ["breakfast", "lunch", "dinner"]:
            mt_indices = candidate_foods.index[candidate_foods["meal_type"] == mt].tolist()
            mt_mapped = [candidate_foods.index.get_loc(idx) for idx in mt_indices]
            if mt_mapped:
                prob += pulp.lpSum(x[i] for i in mt_mapped) >= 1

        # Solve
        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        if prob.status != 1:
            # Fallback: relax constraints and pick top scored foods
            return self._greedy_fallback(candidate_foods, food_scores, calorie_target)

        # Extract results
        selected_indices = [i for i in range(n) if x[i].varValue and x[i].varValue > 0.5]
        selected_foods = candidate_foods.iloc[selected_indices].copy()
        selected_foods["score"] = food_scores[selected_indices]

        meals = {}
        for mt in ["breakfast", "lunch", "dinner", "snack"]:
            mt_foods = selected_foods[selected_foods["meal_type"] == mt]
            if not mt_foods.empty:
                meals[mt] = mt_foods[["food_id", "name", "calories", "protein_g",
                                       "carbs_g", "fat_g", "score"]].to_dict("records")

        totals = {
            "calories": float(selected_foods["calories"].sum()),
            "protein_g": float(selected_foods.get("protein_g", pd.Series([0])).sum()),
            "carbs_g": float(selected_foods.get("carbs_g", pd.Series([0])).sum()),
            "fat_g": float(selected_foods.get("fat_g", pd.Series([0])).sum()),
            "fiber_g": float(selected_foods.get("fiber_g", pd.Series([0])).sum()),
            "sodium_mg": float(selected_foods.get("sodium_mg", pd.Series([0])).sum()),
            "sugar_g": float(selected_foods.get("sugar_g", pd.Series([0])).sum()),
            "n_items": len(selected_indices),
        }

        return {"meals": meals, "totals": totals, "status": "optimal"}

    def _greedy_fallback(self, candidate_foods: pd.DataFrame,
                         food_scores: np.ndarray,
                         calorie_target: float) -> dict:
        order = np.argsort(-food_scores)
        selected = []
        total_cal = 0.0

        for idx in order:
            cal = candidate_foods.iloc[idx]["calories"]
            if total_cal + cal > calorie_target * 1.1:
                continue
            selected.append(idx)
            total_cal += cal
            if total_cal >= calorie_target * 0.9 and len(selected) >= 4:
                break
            if len(selected) >= 8:
                break

        sel_df = candidate_foods.iloc[selected].copy()
        sel_df["score"] = food_scores[selected]

        meals = {}
        for mt in ["breakfast", "lunch", "dinner", "snack"]:
            mt_foods = sel_df[sel_df["meal_type"] == mt]
            if not mt_foods.empty:
                meals[mt] = mt_foods[["food_id", "name", "calories", "score"]].to_dict("records")

        return {
            "meals": meals,
            "totals": {"calories": float(sel_df["calories"].sum()), "n_items": len(selected)},
            "status": "greedy_fallback",
        }


class UserTasteProfile:

    def __init__(self, embedding_dim: int = 8, decay: float = 0.9):
        self.embedding = np.zeros(embedding_dim, dtype=np.float32)
        self.decay = decay
        self.n_updates = 0
        self.cuisine_counts: dict[str, int] = {}
        self.disliked_food_ids: set[int] = set()

    def update(self, food_embedding: np.ndarray, liked: bool = True):
        """Exponential moving average update from a consumed food."""
        if liked:
            self.embedding = self.decay * self.embedding + (1 - self.decay) * food_embedding
            self.n_updates += 1
        # else: no update for disliked foods (they go to exclusion list)

    def update_cuisine(self, cuisine: str):
        self.cuisine_counts[cuisine] = self.cuisine_counts.get(cuisine, 0) + 1

    def add_dislike(self, food_id: int):
        self.disliked_food_ids.add(food_id)

    def preferred_cuisine(self) -> str:
        if not self.cuisine_counts:
            return "Other"
        return max(self.cuisine_counts, key=self.cuisine_counts.get)

    def to_dict(self) -> dict:
        return {
            "embedding": self.embedding.tolist(),
            "n_updates": self.n_updates,
            "cuisine_counts": self.cuisine_counts,
            "disliked_food_ids": list(self.disliked_food_ids),
        }

    @classmethod
    def from_dict(cls, data: dict, embedding_dim: int = 8) -> "UserTasteProfile":
        profile = cls(embedding_dim=embedding_dim)
        profile.embedding = np.array(data["embedding"], dtype=np.float32)
        profile.n_updates = data.get("n_updates", 0)
        profile.cuisine_counts = data.get("cuisine_counts", {})
        profile.disliked_food_ids = set(data.get("disliked_food_ids", []))
        return profile
