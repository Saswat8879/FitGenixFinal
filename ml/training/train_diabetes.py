import sys, os
import numpy as np
import optuna
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import (
    roc_auc_score, accuracy_score, precision_score,
    recall_score, f1_score, brier_score_loss, classification_report,
)
from xgboost import XGBClassifier

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    DIABETES_XGB_PARAMS, DIABETES_LR_PARAMS, DIABETES_SURROGATE_FEATURES,
    DIABETES_FEATURES, SAVED_MODELS_DIR, PROCESSED_DIR, RANDOM_SEED,
    CV_FOLDS, OPTUNA_TRIALS,
)
from utils import save_sklearn_model, set_seed, logger
from data.preprocess_diabetes import load_and_preprocess_diabetes
from models.diabetes_model import DiabetesRiskModel, DiabetesSurrogateModel


def objective(trial, X_train, y_train):
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 100, 500),
        "max_depth": trial.suggest_int("max_depth", 3, 8),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        "gamma": trial.suggest_float("gamma", 0.0, 0.5),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 1.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
        "scale_pos_weight": trial.suggest_float("scale_pos_weight", 1.0, 3.0),
        "random_state": RANDOM_SEED,
        "eval_metric": "auc",
        "use_label_encoder": False,
        "tree_method": "hist",
    }
    model = XGBClassifier(**params)
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_SEED)
    scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="roc_auc")
    return scores.mean()


def train_diabetes():
    set_seed(RANDOM_SEED)

    # 1. Load & preprocess
    logger.info("Loading and preprocessing diabetes data...")
    data = load_and_preprocess_diabetes()
    X_train, X_test = data["X_train"], data["X_test"]
    y_train, y_test = data["y_train"], data["y_test"]
    feature_names = data["feature_names"]

    # 2. Hyperparameter tuning with Optuna
    logger.info(f"Running Optuna ({OPTUNA_TRIALS} trials)...")
    study = optuna.create_study(direction="maximize")
    study.optimize(
        lambda trial: objective(trial, X_train, y_train),
        n_trials=OPTUNA_TRIALS,
        show_progress_bar=True,
    )
    best_xgb_params = {**DIABETES_XGB_PARAMS, **study.best_params}
    best_xgb_params.pop("use_label_encoder", None)
    best_xgb_params.pop("tree_method", None)
    logger.info(f"Best AUC (CV): {study.best_value:.4f}")
    logger.info(f"Best params: {study.best_params}")

    # 3. Train ensemble
    logger.info("Training ensemble model...")
    model = DiabetesRiskModel(
        xgb_params=best_xgb_params,
        lr_params=DIABETES_LR_PARAMS,
        xgb_weight=0.6,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    # 4. Evaluate
    y_prob = model.predict_proba(X_test)
    y_pred = model.predict(X_test, threshold=0.5)

    metrics = {
        "auc_roc": roc_auc_score(y_test, y_prob),
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "brier_score": brier_score_loss(y_test, y_prob),
    }
    logger.info("=== Diabetes Risk Model — Test Metrics ===")
    for k, v in metrics.items():
        logger.info(f"  {k}: {v:.4f}")
    print("\n" + classification_report(y_test, y_pred, target_names=["No Diabetes", "Diabetes"]))

    # 5. Feature importance
    importances = model.feature_importance()
    named_importances = {
        feature_names[i] if i < len(feature_names) else f"f{i}": float(v)
        for i, (_, v) in enumerate(sorted(importances.items()))
    }
    logger.info(f"Feature importances: {named_importances}")

    # 6. Save
    save_sklearn_model(model, "diabetes_risk_ensemble", SAVED_MODELS_DIR, metadata=metrics)

    # 7. Train surrogate model (app-available features only)
    logger.info("Training surrogate model (limited features)...")
    surrogate_indices = [feature_names.index(f) for f in DIABETES_SURROGATE_FEATURES
                         if f in feature_names]
    if len(surrogate_indices) >= 3:
        X_train_surr = X_train[:, surrogate_indices]
        X_test_surr = X_test[:, surrogate_indices]

        # Generate soft labels from full model
        soft_labels_train = model.predict_proba(X_train)

        surrogate = DiabetesSurrogateModel(xgb_params=best_xgb_params)
        surrogate.fit(X_train_surr, soft_labels_train, verbose=False)

        surr_prob = surrogate.predict_proba(X_test_surr)
        surr_auc = roc_auc_score(y_test, surr_prob)
        logger.info(f"Surrogate AUC: {surr_auc:.4f} (vs full: {metrics['auc_roc']:.4f})")

        save_sklearn_model(surrogate, "diabetes_risk_surrogate", SAVED_MODELS_DIR,
                           metadata={"auc_roc": surr_auc, "features": DIABETES_SURROGATE_FEATURES})
    else:
        logger.warning("Could not map surrogate features — skipping surrogate training")

    logger.info("Diabetes risk model training complete!")
    return metrics


if __name__ == "__main__":
    train_diabetes()
