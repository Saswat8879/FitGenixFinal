"""Singleton loader for all ML model artifacts. Loads once at startup."""
import sys
import logging
from pathlib import Path
from typing import Callable, Any

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
            cls._instance._last_error = None
            cls._instance._component_status = {
                "diabetes": False,
                "embedding": False,
                "exercise": False,
                "meal": False,
                "stress": False,
            }
        return cls._instance

    def _load_component(self, name: str, factory: Callable[[], Any]) -> Any:
        model = factory()
        model.load()
        self._component_status[name] = True
        return model

    def load_all(self):
        if self._loaded:
            return
        self._last_error = None
        self._component_status = {
            "diabetes": False,
            "embedding": False,
            "exercise": False,
            "meal": False,
            "stress": False,
        }

        _ensure_ml_path()

        saved_models_dir = ML_ROOT / "saved_models"
        processed_dir = ML_ROOT / "data" / "processed"
        if not saved_models_dir.exists() or not processed_dir.exists():
            self._loaded = False
            self._last_error = (
                f"ML artifact directories missing. saved_models={saved_models_dir.exists()} "
                f"processed={processed_dir.exists()} (ML_ROOT={ML_ROOT})"
            )
            raise FileNotFoundError(self._last_error)

        try:
            from inference.predict_diabetes_risk import DiabetesRiskPredictor
            from inference.compute_user_embedding import UserEmbeddingPredictor
            from inference.recommend_exercises import ExerciseRecommendationPredictor
            from inference.plan_meals import MealPlanPredictor
            from inference.detect_stress import StressPredictor

            logger.info("Loading ML models from %s", ML_ROOT)
            self.diabetes = self._load_component("diabetes", DiabetesRiskPredictor)
            self.embedding = self._load_component("embedding", UserEmbeddingPredictor)
            self.exercise = self._load_component("exercise", ExerciseRecommendationPredictor)
            self.meal = self._load_component("meal", MealPlanPredictor)
            self.stress = self._load_component("stress", StressPredictor)

            self._loaded = True
            logger.info("All ML models loaded successfully.")
        except Exception as e:
            self._loaded = False
            self._last_error = str(e)
            raise

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def last_error(self) -> str | None:
        return self._last_error

    @property
    def component_status(self) -> dict[str, bool]:
        return dict(self._component_status)


ml_models = MLModels()
