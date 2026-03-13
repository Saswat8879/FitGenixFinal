
import os
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
ML_DIR = ROOT_DIR / "ml"
DATASET_DIR = ROOT_DIR / "datasets"
SAVED_MODELS_DIR = ML_DIR / "saved_models"
DATA_DIR = ML_DIR / "data"

# Dataset paths
DIABETES_CSV = DATASET_DIR / "diabetes.csv"
EXERCISE_CSV = DATASET_DIR / "megaGymDataset.csv"
IFCT_CSV = DATASET_DIR / "ifct2017_compositions.csv"
USDA_DIR = DATASET_DIR / "FoodData_Central_csv_2025-12-18"
WESAD_DIR = DATASET_DIR / "WESAD"

# Synthetic / processed data
SYNTHETIC_DIR = DATA_DIR / "synthetic"
PROCESSED_DIR = DATA_DIR / "processed"

# ── Feature Definitions ─────────────────────────────────────────────

# Model 1: Diabetes Risk
DIABETES_FEATURES = [
    "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
    "Insulin", "BMI", "DiabetesPedigreeFunction", "Age",
]
DIABETES_TARGET = "Outcome"
DIABETES_ZERO_IMPUTE_COLS = [
    "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI",
]
# Surrogate model uses only features available in the app
DIABETES_SURROGATE_FEATURES = ["Age", "BMI", "DiabetesPedigreeFunction", "Pregnancies"]

# Model 2: User Embedding
USER_DEMOGRAPHIC_FEATURES = ["age", "sex", "bmi", "num_conditions", "fitness_level"]
USER_GOAL_FEATURES = [
    "goal_weight_loss", "goal_muscle_gain", "goal_endurance",
    "goal_flexibility", "goal_disease_mgmt",
    "diet_veg", "diet_vegan", "diet_keto",
    "available_time_minutes", "equipment_level",
]
USER_BEHAVIOR_FEATURES = [
    "avg_daily_steps", "avg_active_minutes", "avg_heart_rate",
    "hr_variability", "workout_count_weekly", "workout_completion_rate",
    "avg_workout_duration", "sleep_hours_avg", "sleep_consistency",
    "diet_adherence_rate", "calorie_deviation_pct", "stress_score_avg",
    "pain_score_avg", "mood_score_avg", "days_since_last_workout",
]
USER_FEATURE_DIM = len(USER_DEMOGRAPHIC_FEATURES) + len(USER_GOAL_FEATURES) + len(USER_BEHAVIOR_FEATURES)  # 30
EMBEDDING_DIM = 16

# Model 3: Exercise Recommender
EXERCISE_BODY_PARTS = [
    "Chest", "Back", "Legs", "Arms", "Shoulders",
    "Abdominals", "Full Body", "Other",
]
EXERCISE_EQUIPMENT = ["None", "Bands", "Barbell", "Dumbbell", "Machine"]
EXERCISE_TYPES = ["Strength", "Cardio", "Flexibility"]
EXERCISE_LEVELS = {"Beginner": 1, "Intermediate": 2, "Expert": 3}

# Model 4: Food / Diet
FOOD_NUTRITION_COLS = [
    "calories", "protein_g", "carbs_g", "fat_g", "fiber_g",
    "sugar_g", "sodium_mg", "sat_fat_g", "cholesterol_mg", "potassium_mg",
]
FOOD_DIET_TAGS = [
    "vegetarian", "vegan", "low_gi", "low_sodium",
    "diabetic_friendly", "heart_healthy",
]
MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"]
CUISINE_TYPES = ["Indian", "American", "Mediterranean", "Other"]

# Disease-specific constraints (daily)
DISEASE_CONSTRAINTS = {
    "type2_diabetes": {
        "max_sugar_g": 25, "max_gi": 55, "min_fiber_g": 30,
        "calorie_adjustment": 0,
    },
    "hypertension": {
        "max_sodium_mg": 1500, "min_potassium_mg": 3500,
        "max_sat_fat_pct": 0.06, "calorie_adjustment": 0,
    },
    "obesity": {
        "calorie_adjustment": -500, "min_protein_g_per_kg": 1.2,
        "max_fat_pct": 0.25,
    },
    "fatty_liver": {
        "max_sat_fat_pct": 0.10, "min_fiber_g": 25,
        "max_sugar_g": 30, "calorie_adjustment": -300,
    },
}

# Model 5: Stress Detection
STRESS_HR_FEATURES = [
    "hr_mean_1h", "hr_std_1h", "hr_max_1h", "hr_resting_delta",
    "rmssd_proxy",
]
STRESS_CONTEXT_FEATURES = [
    "steps_last_1h", "time_since_last_activity", "time_of_day_norm",
    "sleep_hours_last_night", "recent_self_report",
]

# ── Hyperparameters ──────────────────────────────────────────────────

# Diabetes XGBoost
DIABETES_XGB_PARAMS = {
    "n_estimators": 200,
    "max_depth": 5,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 3,
    "gamma": 0.1,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "scale_pos_weight": 1.5,  # slight class imbalance
    "eval_metric": "auc",
    "random_state": 42,
}

DIABETES_LR_PARAMS = {
    "C": 1.0,
    "penalty": "l2",
    "max_iter": 1000,
    "random_state": 42,
}

# User Embedding Autoencoder
AUTOENCODER_PARAMS = {
    "hidden_dim": 64,
    "embedding_dim": EMBEDDING_DIM,
    "lr": 1e-3,
    "epochs": 100,
    "batch_size": 256,
    "weight_decay": 1e-5,
}

# Clustering
CLUSTER_K_RANGE = range(4, 16)
CLUSTER_DEFAULT_K = 8

# Exercise Recommender XGBoost
EXERCISE_XGB_PARAMS = {
    "n_estimators": 300,
    "max_depth": 6,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 5,
    "gamma": 0.2,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "eval_metric": "auc",
    "random_state": 42,
}

# Stress RF
STRESS_RF_PARAMS = {
    "n_estimators": 100,
    "max_depth": 10,
    "min_samples_leaf": 5,
    "random_state": 42,
}

# ── Synthetic Data ───────────────────────────────────────────────────
N_SYNTHETIC_USERS = 500
N_SYNTHETIC_DAYS = 90
EXPLORATION_RATE = 0.10  # ε-greedy for exercise exploration

# ── User Archetypes for Synthetic Data ───────────────────────────────
USER_ARCHETYPES = {
    "healthy_active_young": {
        "age_range": (22, 30), "bmi_range": (20, 25), "sex_dist": [0.5, 0.5],
        "conditions": [], "fitness_level": 4,
        "goals": ["muscle_gain", "endurance"],
        "steps_range": (8000, 15000), "sleep_range": (6.5, 8.0),
        "stress_range": (1, 4), "weight": 0.15,
    },
    "healthy_sedentary": {
        "age_range": (25, 40), "bmi_range": (22, 28), "sex_dist": [0.5, 0.5],
        "conditions": [], "fitness_level": 1,
        "goals": ["weight_loss", "endurance"],
        "steps_range": (2000, 5000), "sleep_range": (5.5, 7.5),
        "stress_range": (3, 7), "weight": 0.15,
    },
    "overweight_beginner": {
        "age_range": (30, 50), "bmi_range": (28, 35), "sex_dist": [0.4, 0.6],
        "conditions": ["obesity"], "fitness_level": 1,
        "goals": ["weight_loss"],
        "steps_range": (2000, 6000), "sleep_range": (5, 7),
        "stress_range": (3, 6), "weight": 0.15,
    },
    "diabetic_patient": {
        "age_range": (40, 65), "bmi_range": (26, 38), "sex_dist": [0.5, 0.5],
        "conditions": ["type2_diabetes"], "fitness_level": 2,
        "goals": ["disease_mgmt", "weight_loss"],
        "steps_range": (3000, 7000), "sleep_range": (5, 7.5),
        "stress_range": (3, 7), "weight": 0.12,
    },
    "hypertensive_senior": {
        "age_range": (50, 70), "bmi_range": (25, 34), "sex_dist": [0.5, 0.5],
        "conditions": ["hypertension"], "fitness_level": 2,
        "goals": ["disease_mgmt", "flexibility"],
        "steps_range": (3000, 6000), "sleep_range": (5.5, 7),
        "stress_range": (3, 6), "weight": 0.10,
    },
    "stressed_office_worker": {
        "age_range": (25, 40), "bmi_range": (22, 30), "sex_dist": [0.5, 0.5],
        "conditions": [], "fitness_level": 2,
        "goals": ["weight_loss", "endurance"],
        "steps_range": (3000, 7000), "sleep_range": (4.5, 6.5),
        "stress_range": (5, 9), "weight": 0.12,
    },
    "athletic_intermediate": {
        "age_range": (20, 35), "bmi_range": (22, 27), "sex_dist": [0.6, 0.4],
        "conditions": [], "fitness_level": 4,
        "goals": ["muscle_gain", "endurance"],
        "steps_range": (10000, 18000), "sleep_range": (7, 9),
        "stress_range": (1, 4), "weight": 0.08,
    },
    "post_injury_recovery": {
        "age_range": (25, 50), "bmi_range": (22, 30), "sex_dist": [0.5, 0.5],
        "conditions": ["injury_recovery"], "fitness_level": 1,
        "goals": ["flexibility", "endurance"],
        "steps_range": (1500, 4000), "sleep_range": (6, 8),
        "stress_range": (4, 7), "weight": 0.05,
    },
    "asthma_patient": {
        "age_range": (20, 45), "bmi_range": (21, 28), "sex_dist": [0.5, 0.5],
        "conditions": ["asthma"], "fitness_level": 2,
        "goals": ["endurance", "flexibility"],
        "steps_range": (4000, 8000), "sleep_range": (6, 8),
        "stress_range": (3, 6), "weight": 0.04,
    },
    "diabetic_hypertensive": {
        "age_range": (50, 65), "bmi_range": (28, 38), "sex_dist": [0.5, 0.5],
        "conditions": ["type2_diabetes", "hypertension"], "fitness_level": 1,
        "goals": ["disease_mgmt", "weight_loss"],
        "steps_range": (2000, 5000), "sleep_range": (5, 7),
        "stress_range": (4, 8), "weight": 0.04,
    },
}

# ── General ──────────────────────────────────────────────────────────
RANDOM_SEED = 42
TEST_SIZE = 0.2
VAL_SIZE = 0.1
CV_FOLDS = 5
OPTUNA_TRIALS = 30

# Ensure directories exist
for d in [SAVED_MODELS_DIR, DATA_DIR, SYNTHETIC_DIR, PROCESSED_DIR]:
    d.mkdir(parents=True, exist_ok=True)
