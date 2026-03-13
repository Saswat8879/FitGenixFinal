"""Singleton loader for all ML model artifacts. Loads once at startup."""
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ML_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "ml"


def _ensure_ml_path():
    ml_str = str(ML_ROOT)
    if ml_str not in sys.path:
        sys.path.insert(0, ml_str)


class MLModels:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def load_all(self):
        if self._loaded:
            return
        _ensure_ml_path()

        from inference.predict_diabetes_risk import DiabetesRiskPredictor
        from inference.compute_user_embedding import UserEmbeddingPredictor
        from inference.recommend_exercises import ExerciseRecommendationPredictor
        from inference.plan_meals import MealPlanPredictor
        from inference.detect_stress import StressPredictor

        logger.info("Loading ML models...")
        self.diabetes = DiabetesRiskPredictor()
        self.diabetes.load()

        self.embedding = UserEmbeddingPredictor()
        self.embedding.load()

        self.exercise = ExerciseRecommendationPredictor()
        self.exercise.load()

        self.meal = MealPlanPredictor()
        self.meal.load()

        self.stress = StressPredictor()
        self.stress.load()

        self._loaded = True
        logger.info("All ML models loaded successfully.")

    @property
    def is_loaded(self) -> bool:
        return self._loaded


ml_models = MLModels()
