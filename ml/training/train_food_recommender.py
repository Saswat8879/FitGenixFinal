"""
FitGenix ML — Train Food/Diet Recommender
Builds food embeddings, trains scorer, evaluates meal planner.
Run: python -m ml.training.train_food_recommender
"""
import sys, os
import numpy as np
import pandas as pd
import joblib
from tqdm import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    SAVED_MODELS_DIR, PROCESSED_DIR, SYNTHETIC_DIR, RANDOM_SEED,
    FOOD_NUTRITION_COLS, DISEASE_CONSTRAINTS,
)
from utils import (
    save_sklearn_model, set_seed, logger,
    ndcg_at_k, hit_rate_at_k, constraint_satisfaction_rate,
)
from models.food_recommender import FoodScorer, MealPlanner, UserTasteProfile


def train_food_recommender():
    set_seed(RANDOM_SEED)

    # 1. Load preprocessed food data
    foods_path = PROCESSED_DIR / "foods_clean.csv"
    embeddings_path = PROCESSED_DIR / "food_embeddings.npy"

    if not foods_path.exists():
        logger.error(f"Food data not found at {foods_path}")
        logger.error("Run `python -m ml.data.preprocess_food` first!")
        return

    foods_df = pd.read_csv(foods_path)
    food_embeddings = np.load(embeddings_path)
    logger.info(f"Loaded {len(foods_df)} foods, {food_embeddings.shape[1]}-dim embeddings")

    # 2. Initialize scorer
    scorer = FoodScorer(health_weight=0.6)

    # 3. Evaluate on synthetic meal preferences
    synth_path = SYNTHETIC_DIR / "meal_logs.npz"
    if synth_path.exists():
        synth_data = np.load(synth_path, allow_pickle=True)
        user_profiles = synth_data["user_profiles"]
        meal_logs = synth_data["meal_logs"]
        logger.info(f"Loaded {len(meal_logs)} synthetic meal logs")

        # Evaluate scoring quality
        ndcg_scores = []
        hit_scores = []

        for log_entry in meal_logs[:200]:
            user_idx = int(log_entry["user_idx"])
            consumed_ids = set(log_entry["consumed_food_ids"])
            user_constraints = log_entry.get("constraints", {})
            user_taste = np.random.randn(food_embeddings.shape[1]).astype(np.float32) * 0.1

            # If user has consumed foods, build taste profile
            if consumed_ids:
                consumed_mask = foods_df["food_id"].isin(consumed_ids)
                consumed_embeds = food_embeddings[consumed_mask.values]
                if len(consumed_embeds) > 0:
                    user_taste = consumed_embeds.mean(axis=0)

            # Score all foods
            budget = {"calories": 600, "sodium_mg": 800, "sugar_g": 20}
            scores = []
            for i in range(len(foods_df)):
                food_dict = foods_df.iloc[i].to_dict()
                s = scorer.combined_score(
                    food_dict, food_embeddings[i],
                    user_constraints, user_taste, budget
                )
                scores.append(s)
            scores = np.array(scores)

            # Rank and compute metrics
            ranking = np.argsort(-scores)
            top_ids = foods_df.iloc[ranking[:10]]["food_id"].values

            relevance = np.array([1 if fid in consumed_ids else 0 for fid in top_ids])
            ndcg_scores.append(ndcg_at_k(relevance, k=10))
            hit_scores.append(hit_rate_at_k(top_ids, consumed_ids, k=5))

        avg_ndcg = np.mean(ndcg_scores) if ndcg_scores else 0
        avg_hit = np.mean(hit_scores) if hit_scores else 0
        logger.info(f"  Scoring NDCG@10: {avg_ndcg:.4f}")
        logger.info(f"  Scoring HitRate@5: {avg_hit:.4f}")

    # 4. Test meal planner with constraint satisfaction
    logger.info("Testing meal planner...")
    planner = MealPlanner()

    plan_results = []
    test_scenarios = [
        {"calorie_target": 2000, "constraints": {"min_protein_g": 60, "max_sodium_mg": 2300,
                                                   "max_sugar_g": 50, "min_fiber_g": 20}},
        {"calorie_target": 1800, "constraints": {**DISEASE_CONSTRAINTS["type2_diabetes"],
                                                   "min_protein_g": 55}},
        {"calorie_target": 1600, "constraints": {**DISEASE_CONSTRAINTS["hypertension"],
                                                   "min_protein_g": 50}},
        {"calorie_target": 1500, "constraints": {**DISEASE_CONSTRAINTS["obesity"],
                                                   "min_protein_g": 70}},
    ]

    for scenario in tqdm(test_scenarios, desc="Testing meal planner", unit="scenario"):
        cal = scenario["calorie_target"]
        cons = scenario["constraints"]

        # Score foods for this scenario
        dummy_taste = food_embeddings.mean(axis=0)
        budget = {"calories": cal, "sodium_mg": cons.get("max_sodium_mg", 2300),
                  "sugar_g": cons.get("max_sugar_g", 50)}

        scores = np.array([
            scorer.combined_score(
                foods_df.iloc[i].to_dict(), food_embeddings[i],
                cons, dummy_taste, budget
            )
            for i in range(len(foods_df))
        ])

        # Pick top 50 candidates for planning (ILP speed)
        top_indices = np.argsort(-scores)[:50]
        candidate_df = foods_df.iloc[top_indices].reset_index(drop=True)
        candidate_scores = scores[top_indices]

        plan = planner.plan_day(candidate_df, candidate_scores, cons, cal)

        plan_results.append({
            "total_calories": plan["totals"].get("calories", 0),
            "total_protein_g": plan["totals"].get("protein_g", 0),
            "total_sodium_mg": plan["totals"].get("sodium_mg", 0),
            "total_sugar_g": plan["totals"].get("sugar_g", 0),
            "total_fiber_g": plan["totals"].get("fiber_g", 0),
            "status": plan["status"],
            "n_items": plan["totals"].get("n_items", 0),
        })

        logger.info(f"  Plan ({cal} kcal): {plan['status']}, "
                     f"{plan['totals'].get('n_items', 0)} items, "
                     f"{plan['totals'].get('calories', 0):.0f} kcal")

    # Constraint satisfaction
    sat_rate = sum(1 for p in plan_results if p["status"] == "optimal") / len(plan_results)
    logger.info(f"  Constraint satisfaction rate: {sat_rate:.1%}")

    # 5. Save scorer + config
    save_sklearn_model(scorer, "food_scorer", SAVED_MODELS_DIR,
                       metadata={"health_weight": scorer.health_weight,
                                 "constraint_satisfaction": sat_rate})

    metrics = {
        "ndcg_at_10": float(avg_ndcg) if 'avg_ndcg' in dir() else 0,
        "hit_rate_at_5": float(avg_hit) if 'avg_hit' in dir() else 0,
        "constraint_sat_rate": float(sat_rate),
    }

    logger.info("=== Food Recommender — Metrics ===")
    for k, v in metrics.items():
        logger.info(f"  {k}: {v:.4f}")

    logger.info("Food recommender training complete!")
    return metrics


if __name__ == "__main__":
    train_food_recommender()
