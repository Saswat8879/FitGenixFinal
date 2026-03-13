"""
FitGenix ML — Master Training Pipeline
Runs all steps in order: synthetic data → preprocessing → training → evaluation.

Usage:
    python -m ml.run_all              # Full pipeline
    python -m ml.run_all --step synth # Only synthetic data
    python -m ml.run_all --step train # Only training
    python -m ml.run_all --step eval  # Only evaluation
"""
import argparse
import time
import sys
import os
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(__file__))
from utils import logger, set_seed
from config import RANDOM_SEED


def step_synthetic():
    """Generate all synthetic data."""
    logger.info("=" * 70)
    logger.info("STEP 1: Generating synthetic data")
    logger.info("=" * 70)
    from data.synthetic_generator import generate_all
    return generate_all()


def step_preprocess():
    """Run all preprocessing pipelines."""
    logger.info("=" * 70)
    logger.info("STEP 2: Preprocessing real datasets")
    logger.info("=" * 70)

    results = {}

    try:
        from data.preprocess_diabetes import load_and_preprocess_diabetes
        load_and_preprocess_diabetes()
        results["diabetes"] = "ok"
    except Exception as e:
        logger.warning(f"Diabetes preprocessing failed: {e}")
        results["diabetes"] = str(e)

    try:
        from data.preprocess_exercises import load_and_preprocess_exercises
        load_and_preprocess_exercises()
        results["exercises"] = "ok"
    except Exception as e:
        logger.warning(f"Exercise preprocessing failed: {e}")
        results["exercises"] = str(e)

    try:
        from data.preprocess_food import load_and_preprocess_food
        load_and_preprocess_food()
        results["food"] = "ok"
    except Exception as e:
        logger.warning(f"Food preprocessing failed: {e}")
        results["food"] = str(e)

    return results


def step_train():
    """Train all models."""
    logger.info("=" * 70)
    logger.info("STEP 3: Training all models")
    logger.info("=" * 70)

    results = {}

    try:
        from training.train_diabetes import train_diabetes
        results["diabetes"] = train_diabetes()
    except Exception as e:
        logger.warning(f"Diabetes training failed: {e}")
        results["diabetes"] = str(e)

    try:
        from training.train_user_embedding import train_user_embedding
        results["user_embedding"] = train_user_embedding()
    except Exception as e:
        logger.warning(f"User embedding training failed: {e}")
        results["user_embedding"] = str(e)

    try:
        from training.train_exercise_recommender import train_exercise_recommender
        results["exercise_recommender"] = train_exercise_recommender()
    except Exception as e:
        logger.warning(f"Exercise recommender training failed: {e}")
        results["exercise_recommender"] = str(e)

    try:
        from training.train_food_recommender import train_food_recommender
        results["food_recommender"] = train_food_recommender()
    except Exception as e:
        logger.warning(f"Food recommender training failed: {e}")
        results["food_recommender"] = str(e)

    try:
        from training.train_stress import train_stress
        results["stress"] = train_stress()
    except Exception as e:
        logger.warning(f"Stress training failed: {e}")
        results["stress"] = str(e)

    return results


def step_evaluate():
    """Evaluate all models."""
    logger.info("=" * 70)
    logger.info("STEP 4: Evaluating all models")
    logger.info("=" * 70)
    from evaluation.evaluate_all import evaluate_all
    return evaluate_all()


def main():
    parser = argparse.ArgumentParser(description="FitGenix ML Pipeline")
    parser.add_argument("--step", choices=["synth", "preprocess", "train", "eval", "all"],
                        default="all", help="Which pipeline step to run")
    args = parser.parse_args()

    set_seed(RANDOM_SEED)
    start = time.time()

    steps = []
    if args.step in ("synth", "all"):
        steps.append(("Synthetic data", step_synthetic))
    if args.step in ("preprocess", "all"):
        steps.append(("Preprocessing", step_preprocess))
    if args.step in ("train", "all"):
        steps.append(("Training", step_train))
    if args.step in ("eval", "all"):
        steps.append(("Evaluation", step_evaluate))

    for name, fn in tqdm(steps, desc="Pipeline", unit="step"):
        tqdm.write(f"\n>>> {name}")
        fn()

    elapsed = time.time() - start
    logger.info(f"\nPipeline complete. Total time: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
