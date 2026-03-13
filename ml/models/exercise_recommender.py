"""
FitGenix ML — Exercise Recommender Model
XGBoost-based learning-to-rank + rule-based safety filters.
"""
import numpy as np
from xgboost import XGBClassifier

# ── Disease / injury contraindications ───────────────────────────────
CONTRAINDICATIONS = {
    "hypertension": {
        "avoid_keywords": ["heavy", "overhead press", "valsalva"],
        "max_difficulty": 2,
        "max_cardio_intensity": 0.7,
    },
    "asthma": {
        "avoid_keywords": ["sprint", "hiit"],
        "max_cardio_intensity": 0.6,
    },
    "injury_recovery": {
        "max_difficulty": 1,
        "max_injury_risk": 0.3,
    },
    "type2_diabetes": {
        # Encourage exercise, few restrictions
        "max_difficulty": 3,
    },
    "obesity": {
        "max_difficulty": 2,
        "prefer_low_impact": True,
    },
}


class ExerciseRecommender:
    """
    Hybrid exercise recommender:
    1. Rule-based safety filter (hard constraints)
    2. ML ranker (score each candidate exercise for the user)
    """

    def __init__(self, xgb_params: dict):
        self.ranker = XGBClassifier(
            **xgb_params,
            use_label_encoder=False,
            tree_method="hist",
            objective="binary:logistic",
        )
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray, eval_set=None, verbose=True):
        """
        X: (n_interactions, user_features + exercise_features + pair_features)
        y: binary — 1 = completed & not disliked, 0 = skipped/disliked
        """
        self.ranker.fit(X, y, eval_set=eval_set, verbose=verbose)
        self._fitted = True

    def score(self, X: np.ndarray) -> np.ndarray:
        """Return P(completion & satisfaction) for each user-exercise pair."""
        assert self._fitted, "Ranker not fitted"
        return self.ranker.predict_proba(X)[:, 1]

    @staticmethod
    def rule_filter(exercises_df, user_profile: dict) -> list[int]:
        """
        Apply hard safety filters. Returns list of valid exercise indices.

        user_profile keys:
            conditions: list of str
            equipment_available: list of str
            fitness_level: int (1-5)
        """
        valid = []
        conditions = user_profile.get("conditions", [])
        available_equipment = set(user_profile.get("equipment_available", ["None"]))
        fitness_level = user_profile.get("fitness_level", 2)

        for idx, row in exercises_df.iterrows():
            # Equipment check
            if row["equipment"] not in available_equipment and row["equipment"] != "None":
                continue

            # Difficulty check (user fitness level maps: 1-2 → Beginner, 3 → Intermediate, 4-5 → Expert)
            max_difficulty = min(3, (fitness_level + 1) // 2 + 1)

            # Condition-specific constraints
            blocked = False
            for cond in conditions:
                rules = CONTRAINDICATIONS.get(cond, {})
                cond_max_diff = rules.get("max_difficulty", 3)
                max_difficulty = min(max_difficulty, cond_max_diff)

                max_injury = rules.get("max_injury_risk", 1.0)
                if row.get("injury_risk", 0) > max_injury:
                    blocked = True
                    break

                max_cardio = rules.get("max_cardio_intensity", 1.0)
                if row.get("cardio_intensity", 0) > max_cardio:
                    blocked = True
                    break

                avoid_kw = rules.get("avoid_keywords", [])
                name_lower = str(row.get("name", "")).lower()
                if any(kw in name_lower for kw in avoid_kw):
                    blocked = True
                    break

            if blocked:
                continue

            if row.get("difficulty", 2) > max_difficulty:
                continue

            valid.append(idx)

        return valid

    @staticmethod
    def assemble_workout(scored_exercises: list[dict], user_profile: dict) -> list[dict]:
        """
        From scored candidate list, assemble a balanced workout.

        scored_exercises: list of {"exercise_id", "name", "body_part", "type", "score", ...}
        Returns ordered list of exercises for the day.
        """
        target_count = user_profile.get("exercises_per_workout", 6)
        workout_focus = user_profile.get("today_focus", None)  # e.g., "Chest", "Legs", or None for full body

        # Sort by score descending
        candidates = sorted(scored_exercises, key=lambda x: x["score"], reverse=True)

        selected = []
        body_part_counts: dict[str, int] = {}

        for ex in candidates:
            if len(selected) >= target_count:
                break

            bp = ex.get("body_part", "Other")

            # Enforce focus if specified
            if workout_focus and bp != workout_focus and len(selected) < target_count - 1:
                # Allow 1 off-focus exercise
                if sum(1 for s in selected if s.get("body_part") != workout_focus) >= 1:
                    continue

            # Diversity: max 2 exercises per body part
            if body_part_counts.get(bp, 0) >= 2:
                continue

            selected.append(ex)
            body_part_counts[bp] = body_part_counts.get(bp, 0) + 1

        return selected
