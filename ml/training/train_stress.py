"""
FitGenix ML — Train Stress Detection Model
LOSO cross-validation on WESAD data, then train final model.
Run: python -m ml.training.train_stress
"""
import sys, os
import numpy as np
from tqdm import tqdm
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    roc_auc_score, accuracy_score, f1_score, classification_report,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import STRESS_RF_PARAMS, SAVED_MODELS_DIR, PROCESSED_DIR, RANDOM_SEED
from utils import save_sklearn_model, set_seed, logger
from models.stress_model import StressDetector
from data.preprocess_wesad import preprocess_wesad, STRESS_FEATURE_NAMES


def train_stress():
    set_seed(RANDOM_SEED)

    # 1. Load preprocessed WESAD data
    processed_path = PROCESSED_DIR / "wesad_processed.npz"
    if not processed_path.exists():
        logger.info("WESAD data not preprocessed yet. Running preprocessing...")
        data = preprocess_wesad()
    else:
        data = np.load(processed_path, allow_pickle=True)

    X = data["X"]
    y = data["y"]
    subjects = data["subjects"]

    logger.info(f"Loaded stress data: {X.shape[0]} samples, {X.shape[1]} features")
    logger.info(f"  Stress: {(y==1).sum()}, Non-stress: {(y==0).sum()}")

    # 2. Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 3. LOSO (Leave-One-Subject-Out) cross-validation
    unique_subjects = np.unique(subjects)
    loso_aucs = []
    loso_f1s = []

    logger.info(f"LOSO CV across {len(unique_subjects)} subjects...")
    for test_subj in tqdm(unique_subjects, desc="LOSO CV", unit="subject"):
        test_mask = subjects == test_subj
        train_mask = ~test_mask

        if test_mask.sum() < 5 or train_mask.sum() < 5:
            continue

        X_tr, X_te = X_scaled[train_mask], X_scaled[test_mask]
        y_tr, y_te = y[train_mask], y[test_mask]

        # Need both classes in train and test
        if len(np.unique(y_tr)) < 2 or len(np.unique(y_te)) < 2:
            continue

        detector = StressDetector(rf_params=STRESS_RF_PARAMS)
        detector.fit(X_tr, y_tr)

        y_prob = detector.predict_proba_ml(X_te)
        y_pred = (y_prob >= 0.5).astype(int)

        auc = roc_auc_score(y_te, y_prob)
        f1 = f1_score(y_te, y_pred)
        loso_aucs.append(auc)
        loso_f1s.append(f1)
        logger.info(f"  {test_subj}: AUC={auc:.3f}, F1={f1:.3f}")

    if loso_aucs:
        avg_auc = np.mean(loso_aucs)
        avg_f1 = np.mean(loso_f1s)
        logger.info(f"  LOSO mean AUC: {avg_auc:.4f} ± {np.std(loso_aucs):.4f}")
        logger.info(f"  LOSO mean F1:  {avg_f1:.4f} ± {np.std(loso_f1s):.4f}")
    else:
        avg_auc = 0.0
        avg_f1 = 0.0
        logger.warning("  No valid LOSO folds — using all data")

    # 4. Train final model on all data
    logger.info("Training final stress model on all data...")
    final_detector = StressDetector(rf_params=STRESS_RF_PARAMS)
    final_detector.fit(X_scaled, y)

    # In-sample check
    y_prob_all = final_detector.predict_proba_ml(X_scaled)
    y_pred_all = (y_prob_all >= 0.5).astype(int)
    insample_auc = roc_auc_score(y, y_prob_all)
    logger.info(f"  In-sample AUC: {insample_auc:.4f}")

    print("\n" + classification_report(y, y_pred_all, target_names=["Non-stress", "Stress"]))

    # 5. Save
    import joblib
    joblib.dump(scaler, PROCESSED_DIR / "stress_scaler.joblib")
    joblib.dump(STRESS_FEATURE_NAMES, PROCESSED_DIR / "stress_feature_names.joblib")

    metrics = {
        "loso_auc_mean": float(avg_auc),
        "loso_f1_mean": float(avg_f1),
        "insample_auc": float(insample_auc),
        "n_subjects": len(unique_subjects),
        "n_samples": len(y),
    }
    save_sklearn_model(final_detector, "stress_detector", SAVED_MODELS_DIR, metadata=metrics)

    logger.info("=== Stress Detection — Metrics ===")
    for k, v in metrics.items():
        logger.info(f"  {k}: {v}")

    logger.info("Stress detection training complete!")
    return metrics


if __name__ == "__main__":
    train_stress()
