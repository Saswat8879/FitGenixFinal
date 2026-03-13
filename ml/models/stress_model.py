"""
FitGenix ML — Stress Detection Model
Random Forest + rule-based heuristic hybrid.
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier


class StressDetector:
    """
    Hybrid stress detector:
    1. ML model (Random Forest) — when HR data is available and model is calibrated
    2. Rule-based heuristic — fallback when data is sparse
    """

    def __init__(self, rf_params: dict, resting_hr: float = 70.0):
        self.rf = RandomForestClassifier(**rf_params)
        self.resting_hr = resting_hr
        self._ml_fitted = False
        self._calibrated = False
        self.stress_threshold = 0.5

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Train RF on HR-derived features."""
        self.rf.fit(X, y)
        self._ml_fitted = True

    def predict_proba_ml(self, X: np.ndarray) -> np.ndarray:
        """ML-based stress probability."""
        assert self._ml_fitted, "RF not fitted"
        return self.rf.predict_proba(X)[:, 1]

    def predict_heuristic(self, hr_mean: float, hr_std: float,
                          steps_last_1h: int, time_since_activity_min: float,
                          sleep_hours: float) -> float:
        """
        Rule-based stress probability when ML model isn't calibrated.
        Returns stress probability [0, 1].
        """
        score = 0.0

        # Elevated HR at rest
        hr_delta = hr_mean - self.resting_hr
        if hr_delta > 15 and steps_last_1h < 200:
            score += 0.35
        elif hr_delta > 10 and steps_last_1h < 500:
            score += 0.2

        # High HR variability can indicate stress
        if hr_std > 8:
            score += 0.15

        # Prolonged sedentary
        if time_since_activity_min > 90:
            score += 0.1

        # Poor sleep
        if sleep_hours < 5:
            score += 0.15
        elif sleep_hours < 6:
            score += 0.1

        return min(1.0, score)

    def predict(self, features: dict) -> dict:
        """
        Unified prediction interface.

        features dict keys:
            hr_features: np.ndarray (8-dim) — for ML model
            hr_mean, hr_std: float — for heuristic
            steps_last_1h: int
            time_since_activity_min: float
            sleep_hours: float

        Returns: {"probability": float, "is_stressed": bool, "method": str, "interventions": list}
        """
        prob = 0.0
        method = "heuristic"

        # Try ML first
        if self._ml_fitted and "hr_features" in features:
            hr_feats = np.array(features["hr_features"]).reshape(1, -1)
            prob = float(self.predict_proba_ml(hr_feats)[0])
            method = "ml"
        else:
            # Heuristic fallback
            prob = self.predict_heuristic(
                hr_mean=features.get("hr_mean", self.resting_hr),
                hr_std=features.get("hr_std", 5.0),
                steps_last_1h=features.get("steps_last_1h", 0),
                time_since_activity_min=features.get("time_since_activity_min", 0),
                sleep_hours=features.get("sleep_hours", 7.0),
            )

        is_stressed = prob >= self.stress_threshold

        # Determine interventions
        interventions = []
        if is_stressed:
            interventions.append("breathing_exercise_4_7_8")
            if features.get("time_since_activity_min", 0) > 60:
                interventions.append("5_minute_walk")
            if features.get("sleep_hours", 7) < 6:
                interventions.append("sleep_hygiene_reminder")
            interventions.append("reduce_workout_intensity")

        return {
            "probability": round(prob, 3),
            "is_stressed": is_stressed,
            "method": method,
            "interventions": interventions,
        }

    def calibrate_with_self_reports(self, predictions: np.ndarray,
                                    self_reports: np.ndarray):
        """
        Adjust threshold based on user self-reports.
        predictions: model probabilities
        self_reports: binary (1=user reported stress)
        """
        if len(predictions) < 10:
            return  # Need minimum data

        # Find threshold that best matches self-reports (maximize F1)
        best_f1, best_thresh = 0, 0.5
        for thresh in np.arange(0.2, 0.8, 0.05):
            preds = (predictions >= thresh).astype(int)
            tp = ((preds == 1) & (self_reports == 1)).sum()
            fp = ((preds == 1) & (self_reports == 0)).sum()
            fn = ((preds == 0) & (self_reports == 1)).sum()
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            if f1 > best_f1:
                best_f1 = f1
                best_thresh = thresh

        self.stress_threshold = best_thresh
        self._calibrated = True

    def update_resting_hr(self, new_resting_hr: float):
        """Update resting HR baseline (should be done periodically)."""
        self.resting_hr = new_resting_hr
