"""
FitGenix ML — Evaluation Metrics Library
Centralized metrics for all models.
"""
import numpy as np
from typing import Optional


def auc_roc(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Compute AUC-ROC score."""
    from sklearn.metrics import roc_auc_score
    if len(np.unique(y_true)) < 2:
        return 0.0
    return float(roc_auc_score(y_true, y_prob))


def brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Brier score (calibration metric, lower = better)."""
    return float(np.mean((y_prob - y_true) ** 2))


def precision_recall_f1(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Compute precision, recall, F1 for binary classification."""
    from sklearn.metrics import precision_score, recall_score, f1_score
    return {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }


def ndcg_at_k(relevance_scores: np.ndarray, k: int = 10) -> float:
    """NDCG@k for a single ranked list."""
    relevance_scores = np.asarray(relevance_scores)[:k]
    if relevance_scores.sum() == 0:
        return 0.0
    dcg = np.sum(relevance_scores / np.log2(np.arange(2, len(relevance_scores) + 2)))
    ideal = np.sort(relevance_scores)[::-1]
    idcg = np.sum(ideal / np.log2(np.arange(2, len(ideal) + 2)))
    return float(dcg / idcg) if idcg > 0 else 0.0


def hit_rate_at_k(top_k_ids: set, ground_truth_ids: set, k: int = 5) -> float:
    """Hit rate: 1 if any top-k prediction is in ground truth."""
    return 1.0 if top_k_ids & ground_truth_ids else 0.0


def silhouette(embeddings: np.ndarray, labels: np.ndarray) -> float:
    """Silhouette score for clustering."""
    from sklearn.metrics import silhouette_score
    if len(np.unique(labels)) < 2:
        return 0.0
    return float(silhouette_score(embeddings, labels, sample_size=min(5000, len(embeddings))))


def reconstruction_error(original: np.ndarray, reconstructed: np.ndarray) -> float:
    """Mean squared reconstruction error for autoencoder."""
    return float(np.mean((original - reconstructed) ** 2))


def constraint_satisfaction_rate(plans: list[dict], constraints: dict) -> float:
    """Fraction of meal plans satisfying all nutritional constraints."""
    if not plans:
        return 0.0
    satisfied = 0
    for plan in plans:
        ok = True
        for key, limit in constraints.items():
            if key.startswith("max_"):
                nutrient = key[4:]
                if plan.get(f"total_{nutrient}", 0) > limit:
                    ok = False
                    break
            elif key.startswith("min_"):
                nutrient = key[4:]
                if plan.get(f"total_{nutrient}", 0) < limit:
                    ok = False
                    break
        if ok:
            satisfied += 1
    return satisfied / len(plans)


def calorie_deviation(planned_cal: float, target_cal: float) -> float:
    """Percentage deviation from calorie target."""
    if target_cal <= 0:
        return 0.0
    return abs(planned_cal - target_cal) / target_cal * 100


# ── Summary Report ───────────────────────────────────────────────────

def format_metrics_report(metrics: dict, model_name: str) -> str:
    """Format a metrics dict into a readable report string."""
    lines = [f"{'='*50}", f"  {model_name} — Evaluation Metrics", f"{'='*50}"]
    for k, v in metrics.items():
        if isinstance(v, float):
            lines.append(f"  {k:30s}: {v:.4f}")
        else:
            lines.append(f"  {k:30s}: {v}")
    lines.append(f"{'='*50}")
    return "\n".join(lines)
