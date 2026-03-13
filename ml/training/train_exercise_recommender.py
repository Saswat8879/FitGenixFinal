"""
FitGenix ML — Train Exercise Recommender
Uses synthetic interaction logs to train XGBoost ranker.
Run: python -m ml.training.train_exercise_recommender
"""
import sys, os
import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import roc_auc_score, accuracy_score

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    EXERCISE_XGB_PARAMS, SAVED_MODELS_DIR, PROCESSED_DIR,
    SYNTHETIC_DIR, RANDOM_SEED, EMBEDDING_DIM,
)
from utils import save_sklearn_model, set_seed, logger, ndcg_at_k
from models.exercise_recommender import ExerciseRecommender


def compute_pair_features(user_embed: np.ndarray, exercise_feat: np.ndarray,
                          user_fitness: int, exercise_difficulty: int,
                          body_part_staleness: float, equipment_match: int) -> np.ndarray:
    """Build feature vector for a single (user, exercise) pair."""
    # Cosine similarity proxy (dot product since embeddings are roughly normalized)
    similarity = np.dot(user_embed[:min(len(exercise_feat), len(user_embed))],
                        exercise_feat[:min(len(exercise_feat), len(user_embed))])
    difficulty_gap = exercise_difficulty - user_fitness
    pair_feats = np.array([similarity, difficulty_gap, body_part_staleness,
                           equipment_match], dtype=np.float32)
    return np.concatenate([user_embed, exercise_feat, pair_feats])


def train_exercise_recommender():
    set_seed(RANDOM_SEED)

    # Load synthetic interaction data
    interactions_path = SYNTHETIC_DIR / "exercise_interactions.npz"
    if not interactions_path.exists():
        logger.error(f"Interactions not found at {interactions_path}")
        logger.error("Run `python -m ml.data.synthetic_generator` first!")
        return

    data = np.load(interactions_path, allow_pickle=True)
    X = data["X"]          # (n_interactions, feature_dim)
    y = data["y"]           # binary labels
    user_ids = data["user_ids"]  # for grouped split

    logger.info(f"Loaded {len(y)} interactions, {X.shape[1]} features")
    logger.info(f"  Positive rate: {y.mean():.3f}")

    # Split by user (no user leakage between train and test)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=RANDOM_SEED)
    train_idx, test_idx = next(gss.split(X, y, groups=user_ids))

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    logger.info(f"Train: {len(y_train)}, Test: {len(y_test)}")

    # Train
    model = ExerciseRecommender(xgb_params=EXERCISE_XGB_PARAMS)
    model.fit(X_train, y_train,
              eval_set=[(X_test, y_test)],
              verbose=False)

    # Evaluate
    y_prob = model.score(X_test)
    y_pred = (y_prob >= 0.5).astype(int)

    auc = roc_auc_score(y_test, y_prob)
    acc = accuracy_score(y_test, y_pred)

    # Compute NDCG@10 per user
    test_user_ids = user_ids[test_idx]
    unique_test_users = np.unique(test_user_ids)
    ndcg_scores = []
    hit_rates = []

    for uid in tqdm(unique_test_users[:100], desc="NDCG eval", unit="user"):  # Sample 100 users
        mask = test_user_ids == uid
        u_scores = y_prob[mask]
        u_labels = y_test[mask]
        if len(u_labels) < 2:
            continue
        # Sort by predicted score, check NDCG
        order = np.argsort(-u_scores)
        ndcg_scores.append(ndcg_at_k(u_labels[order], k=10))
        # Hit rate@5
        top5_labels = u_labels[order[:5]]
        hit_rates.append(float(top5_labels.sum() > 0))

    avg_ndcg = np.mean(ndcg_scores) if ndcg_scores else 0
    avg_hit = np.mean(hit_rates) if hit_rates else 0

    metrics = {
        "auc_roc": float(auc),
        "accuracy": float(acc),
        "ndcg_at_10": float(avg_ndcg),
        "hit_rate_at_5": float(avg_hit),
    }

    logger.info("=== Exercise Recommender — Test Metrics ===")
    for k, v in metrics.items():
        logger.info(f"  {k}: {v:.4f}")

    # Save
    save_sklearn_model(model, "exercise_recommender", SAVED_MODELS_DIR, metadata=metrics)

    logger.info("Exercise recommender training complete!")
    return metrics


if __name__ == "__main__":
    train_exercise_recommender()
