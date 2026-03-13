import numpy as np
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV


class DiabetesRiskModel:


    def __init__(self, xgb_params: dict, lr_params: dict, xgb_weight: float = 0.6):
        self.xgb = XGBClassifier(
            **xgb_params,
            use_label_encoder=False,
            tree_method="hist",  # works on both CPU and GPU
        )
        self.lr = CalibratedClassifierCV(
            LogisticRegression(**lr_params),
            cv=5,
            method="sigmoid",
        )
        self.xgb_weight = xgb_weight
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray,
            eval_set: list | None = None, verbose: bool = True):
        """Train both models."""
        self.xgb.fit(
            X, y,
            eval_set=eval_set or [(X, y)],
            verbose=verbose,
        )
        self.lr.fit(X, y)
        self._fitted = True

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return ensemble probability of diabetes (class 1)."""
        assert self._fitted, "Model not fitted yet"
        p_xgb = self.xgb.predict_proba(X)[:, 1]
        p_lr = self.lr.predict_proba(X)[:, 1]
        return self.xgb_weight * p_xgb + (1 - self.xgb_weight) * p_lr

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Binary prediction with configurable threshold."""
        return (self.predict_proba(X) >= threshold).astype(int)

    def risk_category(self, probability: float) -> str:
        """Map probability to risk bucket."""
        if probability < 0.3:
            return "Low"
        elif probability < 0.6:
            return "Medium"
        else:
            return "High"

    def feature_importance(self) -> dict:
        """Return XGBoost feature importance (gain-based)."""
        return dict(zip(
            [f"f{i}" for i in range(self.xgb.n_features_in_)],
            self.xgb.feature_importances_,
        ))


class DiabetesSurrogateModel:


    def __init__(self, xgb_params: dict):
        self.model = XGBClassifier(
            **xgb_params,
            use_label_encoder=False,
            tree_method="hist",
            objective="binary:logistic",
        )
        self._fitted = False

    def fit(self, X_surrogate: np.ndarray, soft_labels: np.ndarray, verbose: bool = True):

        # Convert soft labels to hard for XGBClassifier training
        # but weight samples by confidence
        hard_labels = (soft_labels >= 0.5).astype(int)
        sample_weights = np.abs(soft_labels - 0.5) * 2  # higher weight for confident predictions
        sample_weights = np.clip(sample_weights, 0.1, 1.0)

        self.model.fit(X_surrogate, hard_labels, sample_weight=sample_weights, verbose=verbose)
        self._fitted = True

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        assert self._fitted, "Surrogate model not fitted"
        return self.model.predict_proba(X)[:, 1]
