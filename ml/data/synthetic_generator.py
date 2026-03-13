"""
FitGenix ML — Synthetic Data Generator
Generates realistic user profiles, exercise interactions, meal logs,
and stress data using archetypes from config.py.

Run: python -m ml.data.synthetic_generator
"""
import sys, os
import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    USER_ARCHETYPES, N_SYNTHETIC_USERS, N_SYNTHETIC_DAYS,
    EXPLORATION_RATE, SYNTHETIC_DIR, PROCESSED_DIR, EXERCISE_CSV,
    USER_DEMOGRAPHIC_FEATURES, USER_GOAL_FEATURES, USER_BEHAVIOR_FEATURES,
    EMBEDDING_DIM, FOOD_NUTRITION_COLS, FOOD_DIET_TAGS, MEAL_TYPES,
    RANDOM_SEED,
)
from utils import set_seed, logger


# ═══════════════════════════════════════════════════════════════════════
#  1. User Profile Generator
# ═══════════════════════════════════════════════════════════════════════

def _sample_user(archetype: dict, rng: np.random.Generator) -> dict:
    """Sample a single user from an archetype distribution."""
    age = rng.integers(*archetype["age_range"])
    bmi = round(rng.uniform(*archetype["bmi_range"]), 1)
    sex = rng.choice([0, 1], p=archetype["sex_dist"])
    fitness_level = archetype["fitness_level"] + rng.integers(-1, 2)
    fitness_level = max(1, min(5, fitness_level))

    goals = archetype["goals"]
    goal_vec = [
        1 if "weight_loss" in goals else 0,
        1 if "muscle_gain" in goals else 0,
        1 if "endurance" in goals else 0,
        1 if "flexibility" in goals else 0,
        1 if "disease_mgmt" in goals else 0,
    ]
    # Diet preferences (random with slight bias)
    diet_veg = rng.choice([0, 1], p=[0.6, 0.4])
    diet_vegan = 1 if diet_veg and rng.random() < 0.2 else 0
    diet_keto = rng.choice([0, 1], p=[0.85, 0.15]) if not diet_veg else 0

    available_time = rng.integers(20, 90)
    equipment_level = rng.integers(0, 4)  # 0=none, 1=bands, 2=dumbbells, 3=full gym

    # Behavior features — sampled with archetype-conditioned distributions
    steps_mean = rng.uniform(*archetype["steps_range"])
    sleep_mean = rng.uniform(*archetype["sleep_range"])
    stress_mean = rng.uniform(*archetype["stress_range"])

    # Correlated behavior generation
    avg_daily_steps = max(500, steps_mean + rng.normal(0, 500))
    active_minutes = max(5, avg_daily_steps / 120 + rng.normal(0, 10))
    avg_hr = 60 + (10 - fitness_level * 1.5) + bmi * 0.3 + rng.normal(0, 4)
    hr_variability = max(10, 50 - stress_mean * 3 + rng.normal(0, 5))
    workouts_weekly = max(0, min(7, fitness_level - 1 + rng.integers(-1, 2)))
    completion_rate = min(1.0, max(0.1, 0.5 + fitness_level * 0.1 + rng.normal(0, 0.1)))
    workout_duration = max(15, available_time * completion_rate + rng.normal(0, 10))
    sleep_hours = max(3, sleep_mean + rng.normal(0, 0.5))
    sleep_consistency = max(0, min(1, 0.6 + rng.normal(0, 0.15)))
    diet_adherence = max(0, min(1, 0.4 + fitness_level * 0.1 + rng.normal(0, 0.15)))
    calorie_deviation = max(-30, min(30, rng.normal(0, 10)))
    pain_score = max(0, min(10, 2 + rng.normal(0, 2)))
    mood_score = max(1, min(10, 7 - stress_mean * 0.3 + rng.normal(0, 1.5)))
    days_since_workout = max(0, 7 - workouts_weekly + rng.integers(-1, 3))

    profile = np.array([
        # Demographics
        age, sex, bmi, len(archetype["conditions"]), fitness_level,
        # Goals
        *goal_vec, diet_veg, diet_vegan, diet_keto, available_time, equipment_level,
        # Behavior
        avg_daily_steps, active_minutes, avg_hr, hr_variability,
        workouts_weekly, completion_rate, workout_duration,
        sleep_hours, sleep_consistency, diet_adherence, calorie_deviation,
        stress_mean, pain_score, mood_score, days_since_workout,
    ], dtype=np.float32)

    meta = {
        "conditions": archetype["conditions"],
        "archetype_goals": goals,
        "equipment_level": int(equipment_level),
        "fitness_level": int(fitness_level),
    }
    return profile, meta


def generate_user_profiles(n_users: int, rng: np.random.Generator):
    """Generate n_users profiles distributed across archetypes."""
    archetypes = list(USER_ARCHETYPES.keys())
    weights = np.array([USER_ARCHETYPES[a]["weight"] for a in archetypes])
    weights = weights / weights.sum()

    profiles = []
    metas = []
    assignments = rng.choice(len(archetypes), size=n_users, p=weights)

    for i in tqdm(range(n_users), desc="Generating users", unit="user"):
        arch_name = archetypes[assignments[i]]
        arch = USER_ARCHETYPES[arch_name]
        profile, meta = _sample_user(arch, rng)
        meta["archetype"] = arch_name
        meta["user_id"] = i
        profiles.append(profile)
        metas.append(meta)

    X = np.stack(profiles)
    logger.info(f"Generated {n_users} user profiles ({X.shape[1]} features)")
    return X, metas


# ═══════════════════════════════════════════════════════════════════════
#  2. Exercise Interaction Generator
# ═══════════════════════════════════════════════════════════════════════

def _load_exercise_catalog():
    """Load the real exercise catalog for feature vectors."""
    df = pd.read_csv(EXERCISE_CSV)
    if df.columns[0] in ("", "Unnamed: 0"):
        df = df.iloc[:, 1:]
    df.columns = [c.strip() for c in df.columns]

    col_map = {
        "Title": "name", "Desc": "description", "Type": "type",
        "BodyPart": "body_part", "Equipment": "equipment",
        "Level": "level", "Rating": "rating",
    }
    df = df.rename(columns=col_map)
    df = df.dropna(subset=["name"]).reset_index(drop=True)

    # Encode type
    type_map = {"Strength": 0, "Cardio": 1, "Stretching": 2, "Flexibility": 2,
                "Plyometrics": 0, "Powerlifting": 0, "Olympic Weightlifting": 0, "Strongman": 0}
    df["type_enc"] = df["type"].map(lambda x: type_map.get(str(x).strip(), 0))

    # Encode difficulty
    level_map = {"Beginner": 1, "Intermediate": 2, "Expert": 3}
    df["difficulty"] = df["level"].map(lambda x: level_map.get(str(x).strip(), 2))

    # Encode body part
    bp_list = ["Chest", "Back", "Legs", "Arms", "Shoulders", "Abdominals", "Full Body"]
    bp_map = {bp: i for i, bp in enumerate(bp_list)}
    df["body_part_enc"] = df["body_part"].map(lambda x: bp_map.get(str(x).strip(), 7))

    # Simple feature vector per exercise: [type_enc, difficulty, body_part_enc, rating_norm]
    rating = pd.to_numeric(df["rating"], errors="coerce").fillna(5.0)
    df["rating_num"] = rating / 10.0

    exercise_features = np.column_stack([
        df["type_enc"].values,
        df["difficulty"].values,
        df["body_part_enc"].values,
        df["rating_num"].values,
    ]).astype(np.float32)

    return df, exercise_features


def generate_exercise_interactions(user_profiles: np.ndarray, user_metas: list,
                                   rng: np.random.Generator, n_days: int = 30):
    """
    Generate synthetic exercise interaction logs.
    Returns X (feature matrix), y (labels), user_ids.
    """
    try:
        exercise_df, exercise_feats = _load_exercise_catalog()
    except Exception as e:
        logger.warning(f"Cannot load exercise catalog: {e}. Generating synthetic exercises.")
        n_ex = 200
        exercise_feats = rng.uniform(0, 1, (n_ex, 4)).astype(np.float32)
        exercise_df = pd.DataFrame({
            "name": [f"exercise_{i}" for i in range(n_ex)],
            "difficulty": rng.integers(1, 4, n_ex),
            "body_part_enc": rng.integers(0, 8, n_ex),
        })

    n_exercises = len(exercise_df)
    n_users = len(user_profiles)

    # Simple user embedding: take first EMBEDDING_DIM features or pad
    user_embeds = np.zeros((n_users, EMBEDDING_DIM), dtype=np.float32)
    for i, prof in enumerate(user_profiles):
        dim = min(EMBEDDING_DIM, len(prof))
        user_embeds[i, :dim] = prof[:dim]

    all_X = []
    all_y = []
    all_uids = []

    for uid in tqdm(range(n_users), desc="Exercise interactions", unit="user"):
        meta = user_metas[uid]
        fitness = meta["fitness_level"]
        n_interactions = rng.integers(n_days // 3, n_days)  # sample some subset of days

        # Pick exercises for this user to interact with
        candidate_idx = rng.choice(n_exercises, size=min(n_interactions * 3, n_exercises), replace=False)

        for eidx in candidate_idx[:n_interactions]:
            ex_feat = exercise_feats[eidx]
            u_embed = user_embeds[uid]

            # Pair features
            difficulty = ex_feat[1]
            difficulty_gap = difficulty - fitness
            body_part_staleness = rng.uniform(0, 1)
            equipment_match = rng.choice([0, 1], p=[0.2, 0.8])

            similarity = np.dot(u_embed[:min(len(ex_feat), EMBEDDING_DIM)],
                                ex_feat[:min(len(ex_feat), EMBEDDING_DIM)])
            pair_feats = np.array([similarity, difficulty_gap, body_part_staleness,
                                   equipment_match], dtype=np.float32)
            x = np.concatenate([u_embed, ex_feat, pair_feats])

            # Label: P(completion) depends on difficulty gap, fitness, similarity
            base_prob = 0.5
            base_prob += -0.15 * difficulty_gap  # harder exercises less likely completed
            base_prob += 0.05 * fitness           # fitter users do better
            base_prob += 0.02 * similarity        # preference alignment
            base_prob += 0.1 * equipment_match    # equipment available
            base_prob = np.clip(base_prob, 0.05, 0.95)

            label = 1 if rng.random() < base_prob else 0

            all_X.append(x)
            all_y.append(label)
            all_uids.append(uid)

    X = np.array(all_X, dtype=np.float32)
    y = np.array(all_y, dtype=np.int32)
    user_ids = np.array(all_uids, dtype=np.int32)

    logger.info(f"Generated {len(y)} exercise interactions, feature_dim={X.shape[1]}")
    logger.info(f"  Positive rate: {y.mean():.3f}")
    return X, y, user_ids


# ═══════════════════════════════════════════════════════════════════════
#  3. Meal Log Generator
# ═══════════════════════════════════════════════════════════════════════

def generate_meal_logs(user_profiles: np.ndarray, user_metas: list,
                       rng: np.random.Generator, n_days: int = 30):
    """
    Generate synthetic meal interaction logs.
    Returns user_meal_logs: list of dicts with food_id, meal_type, rating, nutrients.
    Also saved as meal_logs.npz for training.
    """
    n_users = len(user_profiles)

    # Create a synthetic food catalog (simplified)
    n_foods = 500
    food_ids = np.arange(n_foods)
    food_cals = rng.uniform(50, 800, n_foods).astype(np.float32)
    food_protein = rng.uniform(1, 40, n_foods).astype(np.float32)
    food_carbs = rng.uniform(5, 80, n_foods).astype(np.float32)
    food_fat = rng.uniform(1, 40, n_foods).astype(np.float32)
    food_fiber = rng.uniform(0, 15, n_foods).astype(np.float32)
    food_sugar = rng.uniform(0, 40, n_foods).astype(np.float32)
    food_sodium = rng.uniform(10, 1200, n_foods).astype(np.float32)
    food_sat_fat = rng.uniform(0, 15, n_foods).astype(np.float32)
    food_chol = rng.uniform(0, 150, n_foods).astype(np.float32)
    food_potassium = rng.uniform(50, 800, n_foods).astype(np.float32)

    # Diet tags (probabilistic)
    food_veg = (rng.random(n_foods) < 0.5).astype(np.float32)
    food_vegan = (food_veg * (rng.random(n_foods) < 0.3)).astype(np.float32)
    food_low_gi = (rng.random(n_foods) < 0.3).astype(np.float32)
    food_low_sodium = (food_sodium < 400).astype(np.float32)
    food_diabetic_friendly = (food_low_gi * (food_sugar < 15)).astype(np.float32)
    food_heart_healthy = (food_low_sodium * (food_sat_fat < 5)).astype(np.float32)

    # Meal type assignment
    food_meal_types = rng.choice(len(MEAL_TYPES), n_foods)

    food_features = np.column_stack([
        food_cals, food_protein, food_carbs, food_fat, food_fiber,
        food_sugar, food_sodium, food_sat_fat, food_chol, food_potassium,
        food_veg, food_vegan, food_low_gi, food_low_sodium,
        food_diabetic_friendly, food_heart_healthy,
    ]).astype(np.float32)

    all_logs = []
    all_X = []
    all_y = []
    all_uids = []

    for uid in tqdm(range(n_users), desc="Meal logs", unit="user"):
        meta = user_metas[uid]
        conditions = meta["conditions"]
        is_veg = user_profiles[uid][15] > 0.5  # diet_veg index
        has_diabetes = "type2_diabetes" in conditions
        has_hypertension = "hypertension" in conditions

        # Simple user food embedding (demographic slice)
        u_embed = user_profiles[uid][:EMBEDDING_DIM].astype(np.float32)
        if len(u_embed) < EMBEDDING_DIM:
            u_embed = np.pad(u_embed, (0, EMBEDDING_DIM - len(u_embed)))

        for day in range(n_days):
            # 3-4 meals per day
            n_meals = rng.integers(3, 5)
            for meal_idx in range(n_meals):
                # Pick a candidate food
                fid = rng.integers(0, n_foods)
                f_feat = food_features[fid]

                # Rating logic — higher for diet-appropriate foods
                base_rating = rng.uniform(3, 8)
                if is_veg and food_veg[fid] < 0.5:
                    base_rating -= 3  # Non-veg penalty
                if has_diabetes and food_diabetic_friendly[fid] > 0.5:
                    base_rating += 1
                if has_hypertension and food_heart_healthy[fid] > 0.5:
                    base_rating += 1

                rating = np.clip(base_rating, 1, 10)
                liked = 1 if rating >= 5 else 0

                # Feature vector: user_embed + food_features + context
                context = np.array([meal_idx / 3.0, day / n_days], dtype=np.float32)
                x = np.concatenate([u_embed, f_feat, context])

                all_X.append(x)
                all_y.append(liked)
                all_uids.append(uid)

                all_logs.append({
                    "user_id": uid, "day": day, "meal_type": MEAL_TYPES[meal_idx % len(MEAL_TYPES)],
                    "food_id": int(fid), "rating": float(rating),
                })

    X = np.array(all_X, dtype=np.float32)
    y = np.array(all_y, dtype=np.int32)
    user_ids = np.array(all_uids, dtype=np.int32)

    logger.info(f"Generated {len(y)} meal interactions, feature_dim={X.shape[1]}")
    logger.info(f"  Positive rate: {y.mean():.3f}")
    return X, y, user_ids, food_features, all_logs


# ═══════════════════════════════════════════════════════════════════════
#  4. Stress Data Generator
# ═══════════════════════════════════════════════════════════════════════

def generate_stress_data(user_profiles: np.ndarray, user_metas: list,
                         rng: np.random.Generator, samples_per_user: int = 20):
    """
    Generate synthetic stress samples from user profiles.
    Uses archetype stress_range to condition distributions.
    """
    all_X = []
    all_y = []
    all_subjects = []

    for uid, (profile, meta) in tqdm(enumerate(zip(user_profiles, user_metas)),
                                     total=len(user_profiles),
                                     desc="Stress data", unit="user"):
        arch_name = meta.get("archetype", "healthy_active_young")
        arch = USER_ARCHETYPES.get(arch_name, USER_ARCHETYPES["healthy_active_young"])
        stress_low, stress_high = arch["stress_range"]
        stress_base = (stress_low + stress_high) / 2.0

        for _ in range(samples_per_user):
            # Is this a stressed moment?
            is_stressed = rng.random() < (stress_base / 10.0)

            if is_stressed:
                hr_mean = rng.uniform(80, 110) + rng.normal(0, 5)
                hr_std = rng.uniform(8, 20)
                hr_max = hr_mean + rng.uniform(15, 40)
                rmssd = rng.uniform(15, 35)
            else:
                hr_mean = rng.uniform(60, 85) + rng.normal(0, 4)
                hr_std = rng.uniform(3, 10)
                hr_max = hr_mean + rng.uniform(5, 20)
                rmssd = rng.uniform(30, 70)

            hr_range = hr_max - hr_mean + rng.uniform(-3, 3)
            signal_energy = rng.uniform(0.3, 0.9) if is_stressed else rng.uniform(0.1, 0.5)
            zcr = rng.uniform(0.1, 0.4)
            peak_rate = hr_mean / 60.0 + rng.normal(0, 0.05)

            features = np.array([
                hr_mean, hr_std, hr_max, hr_range,
                rmssd, signal_energy, zcr, peak_rate,
            ], dtype=np.float32)

            all_X.append(features)
            all_y.append(int(is_stressed))
            all_subjects.append(uid)

    X = np.array(all_X, dtype=np.float32)
    y = np.array(all_y, dtype=np.int32)
    subjects = np.array(all_subjects, dtype=np.int32)

    logger.info(f"Generated {len(y)} stress samples: {y.sum()} stress, {(1-y).sum()} non-stress")
    return X, y, subjects


# ═══════════════════════════════════════════════════════════════════════
#  Main — Generate All Synthetic Data
# ═══════════════════════════════════════════════════════════════════════

def generate_all():
    set_seed(RANDOM_SEED)
    rng = np.random.default_rng(RANDOM_SEED)

    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # ── 1. User profiles ──
    logger.info("=" * 60)
    logger.info("Generating user profiles...")
    user_profiles, user_metas = generate_user_profiles(N_SYNTHETIC_USERS, rng)
    np.save(SYNTHETIC_DIR / "user_profiles.npy", user_profiles)

    import json
    with open(SYNTHETIC_DIR / "user_metas.json", "w") as f:
        json.dump(user_metas, f, indent=2)
    logger.info(f"  Saved user_profiles.npy ({user_profiles.shape})")

    # ── 2. Exercise interactions ──
    logger.info("=" * 60)
    logger.info("Generating exercise interactions...")
    ex_X, ex_y, ex_uids = generate_exercise_interactions(
        user_profiles, user_metas, rng, n_days=N_SYNTHETIC_DAYS // 3,
    )
    np.savez_compressed(
        SYNTHETIC_DIR / "exercise_interactions.npz",
        X=ex_X, y=ex_y, user_ids=ex_uids,
    )
    logger.info(f"  Saved exercise_interactions.npz ({ex_X.shape})")

    # ── 3. Meal logs ──
    logger.info("=" * 60)
    logger.info("Generating meal logs...")
    meal_X, meal_y, meal_uids, food_features, meal_logs = generate_meal_logs(
        user_profiles, user_metas, rng, n_days=N_SYNTHETIC_DAYS // 3,
    )
    np.savez_compressed(
        SYNTHETIC_DIR / "meal_logs.npz",
        X=meal_X, y=meal_y, user_ids=meal_uids,
        food_features=food_features,
    )
    logger.info(f"  Saved meal_logs.npz ({meal_X.shape})")

    # ── 4. Stress data ──
    logger.info("=" * 60)
    logger.info("Generating stress data...")
    stress_X, stress_y, stress_subjects = generate_stress_data(
        user_profiles, user_metas, rng, samples_per_user=20,
    )
    np.savez_compressed(
        PROCESSED_DIR / "wesad_processed.npz",
        X=stress_X, y=stress_y, subjects=stress_subjects,
    )
    logger.info(f"  Saved wesad_processed.npz ({stress_X.shape})")

    # ── Summary ──
    logger.info("=" * 60)
    logger.info("Synthetic data generation complete:")
    logger.info(f"  Users:               {user_profiles.shape[0]}")
    logger.info(f"  Exercise interactions:{ex_X.shape[0]}")
    logger.info(f"  Meal interactions:    {meal_X.shape[0]}")
    logger.info(f"  Stress samples:       {stress_X.shape[0]}")
    logger.info(f"  Output: {SYNTHETIC_DIR}")

    return {
        "n_users": user_profiles.shape[0],
        "n_exercise_interactions": ex_X.shape[0],
        "n_meal_interactions": meal_X.shape[0],
        "n_stress_samples": stress_X.shape[0],
    }


if __name__ == "__main__":
    generate_all()
