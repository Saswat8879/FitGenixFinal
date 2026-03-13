import os
import json
import logging
import numpy as np
import joblib
from pathlib import Path
from datetime import datetime

import torch

logger = logging.getLogger("fitgenix_ml")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


# ── Device Selection ─────────────────────────────────────────────────

def get_device() -> torch.device:
    """Auto-detect CUDA, fallback to CPU."""
    if torch.cuda.is_available():
        dev = torch.device("cuda")
        logger.info(f"Using CUDA: {torch.cuda.get_device_name(0)}")
    else:
        dev = torch.device("cpu")
        logger.info("CUDA not available — using CPU")
    return dev


DEVICE = get_device()


# ── Model Persistence ────────────────────────────────────────────────

def save_sklearn_model(model, name: str, directory: Path, metadata: dict | None = None):
    directory.mkdir(parents=True, exist_ok=True)
    model_path = directory / f"{name}.joblib"
    meta_path = directory / f"{name}_meta.json"

    joblib.dump(model, model_path)
    meta = {
        "name": name,
        "saved_at": datetime.now().isoformat(),
        "type": type(model).__name__,
        **(metadata or {}),
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    logger.info(f"Saved sklearn model → {model_path}")
    return model_path


def load_sklearn_model(name: str, directory: Path):
    model_path = directory / f"{name}.joblib"
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    model = joblib.load(model_path)
    logger.info(f"Loaded sklearn model ← {model_path}")
    return model


def save_torch_model(model: torch.nn.Module, name: str, directory: Path,
                     metadata: dict | None = None):
    directory.mkdir(parents=True, exist_ok=True)
    model_path = directory / f"{name}.pt"
    meta_path = directory / f"{name}_meta.json"

    torch.save(model.state_dict(), model_path)
    meta = {
        "name": name,
        "saved_at": datetime.now().isoformat(),
        "type": type(model).__name__,
        **(metadata or {}),
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    logger.info(f"Saved PyTorch model → {model_path}")
    return model_path


def load_torch_model(model: torch.nn.Module, name: str, directory: Path):
    model_path = directory / f"{name}.pt"
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    model.load_state_dict(torch.load(model_path, map_location=DEVICE, weights_only=True))
    model.eval()
    logger.info(f"Loaded PyTorch model ← {model_path}")
    return model


# ── Metrics Helpers ──────────────────────────────────────────────────

def ndcg_at_k(relevance_scores: np.ndarray, k: int = 10) -> float:
    relevance_scores = np.asarray(relevance_scores)[:k]
    if relevance_scores.sum() == 0:
        return 0.0
    dcg = np.sum(relevance_scores / np.log2(np.arange(2, len(relevance_scores) + 2)))
    ideal = np.sort(relevance_scores)[::-1]
    idcg = np.sum(ideal / np.log2(np.arange(2, len(ideal) + 2)))
    return float(dcg / idcg) if idcg > 0 else 0.0


def hit_rate_at_k(predictions: np.ndarray, ground_truth: set, k: int = 5) -> float:
    top_k = set(predictions[:k])
    return 1.0 if top_k & ground_truth else 0.0


def constraint_satisfaction_rate(plans: list[dict], constraints: dict) -> float:
    satisfied = 0
    for plan in plans:
        ok = True
        if "max_sugar_g" in constraints and plan.get("total_sugar_g", 0) > constraints["max_sugar_g"]:
            ok = False
        if "max_sodium_mg" in constraints and plan.get("total_sodium_mg", 0) > constraints["max_sodium_mg"]:
            ok = False
        if "min_fiber_g" in constraints and plan.get("total_fiber_g", 0) < constraints["min_fiber_g"]:
            ok = False
        if "min_protein_g" in constraints and plan.get("total_protein_g", 0) < constraints["min_protein_g"]:
            ok = False
        if ok:
            satisfied += 1
    return satisfied / len(plans) if plans else 0.0


# ── Data Helpers ─────────────────────────────────────────────────────

def normalize_array(arr: np.ndarray) -> tuple[np.ndarray, float, float]:
    mn, mx = arr.min(), arr.max()
    if mx - mn < 1e-9:
        return np.zeros_like(arr, dtype=np.float32), float(mn), float(mx)
    return ((arr - mn) / (mx - mn)).astype(np.float32), float(mn), float(mx)


def set_seed(seed: int = 42):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    import random
    random.seed(seed)
