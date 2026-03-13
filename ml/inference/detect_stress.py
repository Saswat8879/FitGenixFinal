"""
FitGenix ML — Inference: Stress Detection
Loads stress model and provides real-time stress prediction.
"""
import sys, os
import numpy as np
import joblib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import SAVED_MODELS_DIR, PROCESSED_DIR
from utils import load_sklearn_model, logger


class StressPredictor:
    """Production inference wrapper for stress detection."""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = None
        self._loaded = False

    def load(self):
        """Load trained stress model and scaler."""
        self.model = load_sklearn_model("stress_detector", SAVED_MODELS_DIR)
        self.scaler = joblib.load(PROCESSED_DIR / "stress_scaler.joblib")
        self.feature_names = joblib.load(PROCESSED_DIR / "stress_feature_names.joblib")
        self._loaded = True
        logger.info("StressPredictor loaded.")

    def predict(self, features: dict) -> dict:
        """
        Predict stress from sensor/context features.

        features: {
            # HR features (from Google Fit / wearable)
            hr_mean: float,         # Average heart rate in last window
            hr_std: float,          # HR standard deviation
            hr_max: float,          # Max HR in window
            hr_range: float,        # HR range
            rmssd: float,           # HRV proxy (RMSSD)
            signal_energy: float,   # Signal energy
            zcr: float,             # Zero-crossing rate
            peak_rate: float,       # R-peak rate

            # Context features (optional, for heuristic)
            steps_last_1h: int,
            time_since_activity_min: float,
            sleep_hours: float,
        }

        Returns: {
            probability: float,
            is_stressed: bool,
            method: str ("ml" or "heuristic"),
            interventions: list[str],
        }
        """
        if not self._loaded:
            self.load()

        # Attempt ML prediction with HR feature vector
        hr_feature_keys = ["hr_mean", "hr_std", "hr_max", "hr_range",
                           "rmssd", "signal_energy", "zcr", "peak_rate"]

        has_hr = all(k in features for k in hr_feature_keys)

        if has_hr:
            hr_vector = np.array([features[k] for k in hr_feature_keys], dtype=np.float32)
            features["hr_features"] = hr_vector

        return self.model.predict(features)

    def predict_batch(self, feature_matrix: np.ndarray) -> np.ndarray:
        """
        Batch prediction on pre-assembled feature matrix.

        feature_matrix: (n_samples, 8) HR features
        Returns: (n_samples,) stress probabilities
        """
        if not self._loaded:
            self.load()

        X_scaled = self.scaler.transform(feature_matrix)
        return self.model.predict_proba_ml(X_scaled)

    def calibrate(self, predictions: np.ndarray, self_reports: np.ndarray):
        """Adjust threshold using user self-reports."""
        if not self._loaded:
            self.load()
        self.model.calibrate_with_self_reports(predictions, self_reports)
        logger.info(f"Stress threshold calibrated to {self.model.stress_threshold:.3f}")


if __name__ == "__main__":
    predictor = StressPredictor()
    predictor.load()

    result = predictor.predict({
        "hr_mean": 92.5,
        "hr_std": 12.3,
        "hr_max": 108.0,
        "hr_range": 15.5,
        "rmssd": 25.0,
        "signal_energy": 0.65,
        "zcr": 0.22,
        "peak_rate": 1.54,
        "steps_last_1h": 150,
        "time_since_activity_min": 95,
        "sleep_hours": 5.5,
    })
    print(f"Stress: prob={result['probability']}, stressed={result['is_stressed']}")
    print(f"  Method: {result['method']}, Interventions: {result['interventions']}")
