"""
FitGenix ML — Evaluate All Models
End-to-end evaluation pipeline that runs all 5 models and produces a summary report.

Run: python -m ml.evaluation.evaluate_all
"""
import sys, os
import json
import time
import numpy as np
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import SAVED_MODELS_DIR, PROCESSED_DIR, SYNTHETIC_DIR, RANDOM_SEED
from utils import set_seed, logger
from evaluation.metrics import (
    auc_roc, brier_score, precision_recall_f1, ndcg_at_k,
    silhouette, reconstruction_error, constraint_satisfaction_rate,
    calorie_deviation, format_metrics_report,
)


def evaluate_diabetes():
    """Evaluate diabetes risk model on held-out data."""
    logger.info("Evaluating diabetes risk model...")
    try:
        from inference.predict_diabetes_risk import DiabetesRiskPredictor
        import pandas as pd
        from config import DIABETES_CSV, DIABETES_FEATURES, DIABETES_TARGET

        predictor = DiabetesRiskPredictor()
        predictor.load()

        df = pd.read_csv(DIABETES_CSV)
        X = df[DIABETES_FEATURES].values
        y = df[DIABETES_TARGET].values

        # Use last 20% as test
        split = int(len(y) * 0.8)
        X_test, y_test = X[split:], y[split:]

        probs = []
        for i in range(len(X_test)):
            row = dict(zip(DIABETES_FEATURES, X_test[i]))
            result = predictor.predict(row)
            probs.append(result["probability"])

        probs = np.array(probs)
        preds = (probs >= 0.5).astype(int)

        metrics = {
            "auc_roc": auc_roc(y_test, probs),
            "brier_score": brier_score(y_test, probs),
            **precision_recall_f1(y_test, preds),
            "n_test": len(y_test),
        }
        return metrics
    except Exception as e:
        logger.warning(f"Diabetes evaluation failed: {e}")
        return {"error": str(e)}


def evaluate_user_embedding():
    """Evaluate autoencoder + clustering."""
    logger.info("Evaluating user embedding model...")
    try:
        from inference.compute_user_embedding import UserEmbeddingPredictor

        predictor = UserEmbeddingPredictor()
        predictor.load()

        profiles = np.load(SYNTHETIC_DIR / "user_profiles.npy")
        embeddings = predictor.embed(profiles)

        # Clustering quality
        cluster_labels = predictor.cluster_model.predict(embeddings)
        sil = silhouette(embeddings, cluster_labels)

        # Reconstruction error
        import torch
        x_scaled = predictor.scaler.transform(profiles).astype(np.float32)
        x_tensor = torch.from_numpy(x_scaled).to(predictor.device)
        with torch.no_grad():
            recon, _ = predictor.autoencoder(x_tensor)
        recon_err = reconstruction_error(x_scaled, recon.cpu().numpy())

        metrics = {
            "silhouette_score": sil,
            "reconstruction_mse": recon_err,
            "n_clusters": int(predictor.cluster_model.kmeans.n_clusters),
            "n_users": len(profiles),
        }
        return metrics
    except Exception as e:
        logger.warning(f"User embedding evaluation failed: {e}")
        return {"error": str(e)}


def evaluate_exercise_recommender():
    """Evaluate exercise recommender on synthetic test data."""
    logger.info("Evaluating exercise recommender...")
    try:
        from sklearn.metrics import roc_auc_score
        data = np.load(SYNTHETIC_DIR / "exercise_interactions.npz")
        X, y, user_ids = data["X"], data["y"], data["user_ids"]

        # Split
        split = int(len(y) * 0.8)
        X_test, y_test = X[split:], y[split:]
        uid_test = user_ids[split:]

        from utils import load_sklearn_model
        model = load_sklearn_model("exercise_recommender", SAVED_MODELS_DIR)
        y_prob = model.score(X_test)
        y_pred = (y_prob >= 0.5).astype(int)

        # NDCG per user
        unique_users = np.unique(uid_test)
        ndcg_scores = []
        for uid in unique_users[:100]:
            mask = uid_test == uid
            if mask.sum() < 2:
                continue
            order = np.argsort(-y_prob[mask])
            ndcg_scores.append(ndcg_at_k(y_test[mask][order], k=10))

        metrics = {
            "auc_roc": float(roc_auc_score(y_test, y_prob)),
            "ndcg_at_10": float(np.mean(ndcg_scores)) if ndcg_scores else 0.0,
            **precision_recall_f1(y_test, y_pred),
            "n_test": len(y_test),
        }
        return metrics
    except Exception as e:
        logger.warning(f"Exercise recommender evaluation failed: {e}")
        return {"error": str(e)}


def evaluate_food_recommender():
    """Evaluate meal planner constraints and food scoring."""
    logger.info("Evaluating food recommender...")
    try:
        from inference.plan_meals import MealPlanPredictor

        planner = MealPlanPredictor()
        planner.load()

        scenarios = [
            {"conditions": [], "calorie_target": 2000, "dietary_prefs": []},
            {"conditions": ["type2_diabetes"], "calorie_target": 1800, "dietary_prefs": []},
            {"conditions": ["hypertension"], "calorie_target": 2000, "dietary_prefs": []},
            {"conditions": ["obesity"], "calorie_target": 1500, "dietary_prefs": ["vegetarian"]},
        ]

        results = []
        for scenario in scenarios:
            plan = planner.plan_day(scenario)
            results.append({
                "conditions": scenario["conditions"],
                "n_foods": plan["n_foods"],
                "total_calories": plan["totals"].get("calories", 0),
                "calorie_target": plan["calorie_target"],
                "constraint_satisfied": plan["constraint_satisfaction"],
                "cal_deviation_pct": calorie_deviation(
                    plan["totals"].get("calories", 0), plan["calorie_target"]
                ),
            })

        n_satisfied = sum(1 for r in results if r["constraint_satisfied"])
        avg_cal_dev = np.mean([r["cal_deviation_pct"] for r in results])

        metrics = {
            "constraint_satisfaction_rate": n_satisfied / len(results),
            "avg_calorie_deviation_pct": float(avg_cal_dev),
            "scenarios_tested": len(results),
        }
        return metrics
    except Exception as e:
        logger.warning(f"Food recommender evaluation failed: {e}")
        return {"error": str(e)}


def evaluate_stress_detection():
    """Evaluate stress detection model."""
    logger.info("Evaluating stress detection model...")
    try:
        data = np.load(PROCESSED_DIR / "wesad_processed.npz")
        X, y = data["X"], data["y"]

        split = int(len(y) * 0.8)
        X_test, y_test = X[split:], y[split:]

        from inference.detect_stress import StressPredictor
        predictor = StressPredictor()
        predictor.load()

        probs = predictor.predict_batch(X_test)
        preds = (probs >= 0.5).astype(int)

        metrics = {
            "auc_roc": auc_roc(y_test, probs),
            "brier_score": brier_score(y_test, probs),
            **precision_recall_f1(y_test, preds),
            "n_test": len(y_test),
        }
        return metrics
    except Exception as e:
        logger.warning(f"Stress detection evaluation failed: {e}")
        return {"error": str(e)}


def evaluate_all():
    """Run all evaluations and produce summary report."""
    set_seed(RANDOM_SEED)
    start = time.time()

    evaluators = {
        "Diabetes Risk Model": evaluate_diabetes,
        "User Embedding & Clustering": evaluate_user_embedding,
        "Exercise Recommender": evaluate_exercise_recommender,
        "Food/Diet Recommender": evaluate_food_recommender,
        "Stress Detection": evaluate_stress_detection,
    }

    all_metrics = {}
    for name, fn in evaluators.items():
        try:
            metrics = fn()
            all_metrics[name] = metrics
            print(format_metrics_report(metrics, name))
        except Exception as e:
            all_metrics[name] = {"error": str(e)}
            logger.error(f"{name}: {e}")

    elapsed = time.time() - start

    # Save report
    report_path = Path(SAVED_MODELS_DIR) / "evaluation_report.json"
    all_metrics["_meta"] = {"elapsed_seconds": round(elapsed, 2)}
    report_path.write_text(json.dumps(all_metrics, indent=2))
    logger.info(f"Evaluation report saved to {report_path}")
    logger.info(f"Total evaluation time: {elapsed:.1f}s")

    return all_metrics


if __name__ == "__main__":
    evaluate_all()
