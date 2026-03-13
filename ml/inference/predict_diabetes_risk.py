"""
FitGenix ML — Inference: Diabetes Risk Prediction
Loads saved models and provides fast single-user prediction.
"""
import sys, os
import numpy as np
import joblib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import SAVED_MODELS_DIR, PROCESSED_DIR, DIABETES_SURROGATE_FEATURES, DIABETES_FEATURES
from utils import load_sklearn_model, logger


class DiabetesRiskPredictor:
    """Production inference wrapper for diabetes risk model."""

    def __init__(self):
        self.model = None
        self.surrogate = None
        self.scaler = None
        self.imputer = None
        self.feature_names = None
        self._loaded = False

    def load(self):
        """Load trained models and preprocessors from disk."""
        self.model = load_sklearn_model("diabetes_risk_ensemble", SAVED_MODELS_DIR)
        self.scaler = joblib.load(PROCESSED_DIR / "diabetes_scaler.joblib")
        self.imputer = joblib.load(PROCESSED_DIR / "diabetes_imputer.joblib")
        self.feature_names = joblib.load(PROCESSED_DIR / "diabetes_feature_names.joblib")

        # Try surrogate
        try:
            self.surrogate = load_sklearn_model("diabetes_risk_surrogate", SAVED_MODELS_DIR)
        except FileNotFoundError:
            logger.warning("Surrogate model not found — using full model only")

        self._loaded = True
        logger.info("DiabetesRiskPredictor loaded.")

    def predict(self, user_data: dict) -> dict:
        """
        Predict diabetes risk for a single user.

        user_data: dict with keys from DIABETES_FEATURES
            (Pregnancies, Glucose, BloodPressure, SkinThickness,
             Insulin, BMI, DiabetesPedigreeFunction, Age)
            Missing values should be set to 0 or omitted.

        Returns: {"probability": float, "risk_category": str, "method": str}
        """
        if not self._loaded:
            self.load()

        # Check whether we have enough features for full model
        available = set(user_data.keys())
        has_full = all(f in available for f in DIABETES_FEATURES)

        if has_full:
            return self._predict_full(user_data)
        elif self.surrogate is not None:
            return self._predict_surrogate(user_data)
        else:
            return self._predict_full(user_data)  # try anyway with defaults

    def _predict_full(self, user_data: dict) -> dict:
        """Full model prediction with all features."""
        # Build feature vector in correct order
        x = np.array([[user_data.get(f, 0) for f in self.feature_names]], dtype=np.float64)
        x = self.scaler.transform(x)
        prob = float(self.model.predict_proba(x)[0])
        return {
            "probability": round(prob, 4),
            "risk_category": self.model.risk_category(prob),
            "method": "full_ensemble",
        }

    def _predict_surrogate(self, user_data: dict) -> dict:
        """Surrogate model prediction with limited features."""
        x = np.array([[
            user_data.get("Age", 30),
            user_data.get("BMI", 25),
            user_data.get("DiabetesPedigreeFunction", 0.5),
            user_data.get("Pregnancies", 0),
        ]], dtype=np.float64)
        prob = float(self.surrogate.predict_proba(x)[0])
        return {
            "probability": round(prob, 4),
            "risk_category": "Low" if prob < 0.3 else ("Medium" if prob < 0.6 else "High"),
            "method": "surrogate",
        }


# ── Standalone usage ─────────────────────────────────────────────────
if __name__ == "__main__":
    predictor = DiabetesRiskPredictor()
    predictor.load()

    # Example prediction
    result = predictor.predict({
        "Pregnancies": 3, "Glucose": 148, "BloodPressure": 72,
        "SkinThickness": 35, "Insulin": 0, "BMI": 33.6,
        "DiabetesPedigreeFunction": 0.627, "Age": 50,
    })
    print(f"Diabetes risk: {result}")
