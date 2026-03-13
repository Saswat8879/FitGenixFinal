"""
FitGenix ML — Inference: Exercise Recommendation
Loads XGBoost ranker and applies rule-based safety filters.
"""
import sys, os
import numpy as np
import pandas as pd
import joblib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import SAVED_MODELS_DIR, PROCESSED_DIR, EXERCISE_XGB_PARAMS, EMBEDDING_DIM
from utils import load_sklearn_model, logger
from models.exercise_recommender import ExerciseRecommender


class ExerciseRecommendationPredictor:
    """Production inference wrapper for exercise recommendation."""

    def __init__(self):
        self.model = None
        self.exercise_df = None
        self.exercise_features = None
        self._loaded = False

    def load(self):
        """Load trained recommender and exercise catalog."""
        self.model = load_sklearn_model("exercise_recommender", SAVED_MODELS_DIR)
        self.exercise_features = np.load(PROCESSED_DIR / "exercise_features.npy")
        self.exercise_df = pd.read_csv(PROCESSED_DIR / "exercises_clean.csv")
        self._loaded = True
        logger.info(f"ExerciseRecommendationPredictor loaded. {len(self.exercise_df)} exercises.")

    def recommend(self, user_profile: dict, user_embedding: np.ndarray,
                  top_k: int = 10) -> list[dict]:
        """
        Recommend exercises for a user.

        user_profile: {
            conditions: list[str],
            fitness_level: int (1-5),
            equipment_available: list[str],
            exercises_per_workout: int,
            today_focus: str | None,
        }
        user_embedding: 16-dim embedding from UserEmbeddingPredictor

        Returns: list of dicts with exercise details + scores.
        """
        if not self._loaded:
            self.load()

        # 1. Rule-based filtering
        valid_indices = ExerciseRecommender.rule_filter(self.exercise_df, user_profile)
        if not valid_indices:
            logger.warning("No exercises passed safety filter.")
            return []

        # 2. Score each valid exercise with ML model
        if user_embedding.shape[0] < EMBEDDING_DIM:
            user_embedding = np.pad(user_embedding, (0, EMBEDDING_DIM - len(user_embedding)))

        scored = []
        fitness = user_profile.get("fitness_level", 2)

        for idx in valid_indices:
            ex_feat = self.exercise_features[idx]
            difficulty = self.exercise_df.iloc[idx].get("difficulty", 2)

            difficulty_gap = difficulty - fitness
            body_part_staleness = 0.5  # default, could be personalized
            equipment_match = 1

            similarity = np.dot(
                user_embedding[:min(len(ex_feat), EMBEDDING_DIM)],
                ex_feat[:min(len(ex_feat), EMBEDDING_DIM)],
            )
            pair_feats = np.array([similarity, difficulty_gap, body_part_staleness,
                                   equipment_match], dtype=np.float32)
            x = np.concatenate([user_embedding, ex_feat, pair_feats]).reshape(1, -1)

            try:
                score = float(self.model.score(x)[0])
            except Exception:
                score = 0.5  # fallback

            row = self.exercise_df.iloc[idx]
            scored.append({
                "exercise_id": int(idx),
                "name": str(row.get("name", "")),
                "body_part": str(row.get("body_part", "Other")),
                "type": str(row.get("type", "Strength")),
                "difficulty": int(row.get("difficulty", 2)),
                "score": round(score, 4),
            })

        # 3. Assemble diverse workout
        workout = ExerciseRecommender.assemble_workout(scored, user_profile)

        # If workout is smaller than top_k, fill from remaining scored
        if len(workout) < top_k:
            used_ids = {e["exercise_id"] for e in workout}
            remaining = sorted(
                [e for e in scored if e["exercise_id"] not in used_ids],
                key=lambda x: x["score"], reverse=True,
            )
            workout.extend(remaining[:top_k - len(workout)])

        return workout[:top_k]


if __name__ == "__main__":
    predictor = ExerciseRecommendationPredictor()
    predictor.load()

    dummy_profile = {
        "conditions": [],
        "fitness_level": 3,
        "equipment_available": ["None", "Dumbbell"],
        "exercises_per_workout": 6,
        "today_focus": None,
    }
    dummy_embed = np.random.randn(EMBEDDING_DIM).astype(np.float32)

    recs = predictor.recommend(dummy_profile, dummy_embed)
    for r in recs:
        print(f"  {r['name']}: score={r['score']:.3f} ({r['body_part']}, {r['type']})")
