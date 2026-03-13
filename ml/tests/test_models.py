"""
FitGenix ML — Test Suite
Tests for all 5 ML models: unit tests on model classes, integration tests on inference pipelines.
Run: python -m pytest ml/tests/test_models.py -v
"""
import sys
import os
import pytest
import numpy as np
import pandas as pd
import torch

# Ensure ml/ is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import (
    SAVED_MODELS_DIR, PROCESSED_DIR,
    DIABETES_FEATURES, DIABETES_XGB_PARAMS, DIABETES_LR_PARAMS,
    USER_FEATURE_DIM, EMBEDDING_DIM, AUTOENCODER_PARAMS,
    EXERCISE_XGB_PARAMS, STRESS_RF_PARAMS,
    DISEASE_CONSTRAINTS, MEAL_TYPES,
)


# ═════════════════════════════════════════════════════════════════════
#  Model 1: Diabetes Risk
# ═════════════════════════════════════════════════════════════════════

class TestDiabetesModel:
    """Unit tests for DiabetesRiskModel and DiabetesSurrogateModel."""

    def test_model_fit_and_predict(self):
        from models.diabetes_model import DiabetesRiskModel
        model = DiabetesRiskModel(DIABETES_XGB_PARAMS, DIABETES_LR_PARAMS)
        X = np.random.rand(200, len(DIABETES_FEATURES))
        y = np.random.randint(0, 2, 200)

        model.fit(X, y, verbose=False)
        assert model._fitted

        probs = model.predict_proba(X)
        assert probs.shape == (200,)
        assert np.all((probs >= 0) & (probs <= 1))

    def test_predict_binary(self):
        from models.diabetes_model import DiabetesRiskModel
        model = DiabetesRiskModel(DIABETES_XGB_PARAMS, DIABETES_LR_PARAMS)
        X = np.random.rand(100, len(DIABETES_FEATURES))
        y = np.random.randint(0, 2, 100)
        model.fit(X, y, verbose=False)

        preds = model.predict(X, threshold=0.5)
        assert set(np.unique(preds)).issubset({0, 1})
        assert preds.shape == (100,)

    def test_risk_category(self):
        from models.diabetes_model import DiabetesRiskModel
        model = DiabetesRiskModel(DIABETES_XGB_PARAMS, DIABETES_LR_PARAMS)
        assert model.risk_category(0.1) == "Low"
        assert model.risk_category(0.4) == "Medium"
        assert model.risk_category(0.8) == "High"

    def test_feature_importance(self):
        from models.diabetes_model import DiabetesRiskModel
        model = DiabetesRiskModel(DIABETES_XGB_PARAMS, DIABETES_LR_PARAMS)
        X = np.random.rand(100, len(DIABETES_FEATURES))
        y = np.random.randint(0, 2, 100)
        model.fit(X, y, verbose=False)

        fi = model.feature_importance()
        assert isinstance(fi, dict)
        assert len(fi) == len(DIABETES_FEATURES)

    def test_surrogate_model_fit_and_predict(self):
        from models.diabetes_model import DiabetesSurrogateModel
        model = DiabetesSurrogateModel(DIABETES_XGB_PARAMS)
        X = np.random.rand(100, 4)
        soft_labels = np.random.rand(100)
        model.fit(X, soft_labels, verbose=False)
        assert model._fitted

        probs = model.predict_proba(X)
        assert probs.shape == (100,)
        assert np.all((probs >= 0) & (probs <= 1))

    def test_not_fitted_raises(self):
        from models.diabetes_model import DiabetesRiskModel
        model = DiabetesRiskModel(DIABETES_XGB_PARAMS, DIABETES_LR_PARAMS)
        with pytest.raises(AssertionError):
            model.predict_proba(np.random.rand(1, 8))


class TestDiabetesInference:
    """Integration tests for DiabetesRiskPredictor using saved models."""

    @pytest.fixture(autouse=True)
    def check_models(self):
        model_path = SAVED_MODELS_DIR / "diabetes_risk_ensemble.joblib"
        if not model_path.exists():
            pytest.skip("Diabetes model not trained yet")

    def test_full_prediction(self):
        from inference.predict_diabetes_risk import DiabetesRiskPredictor
        predictor = DiabetesRiskPredictor()
        predictor.load()

        result = predictor.predict({
            "Pregnancies": 3, "Glucose": 148, "BloodPressure": 72,
            "SkinThickness": 35, "Insulin": 0, "BMI": 33.6,
            "DiabetesPedigreeFunction": 0.627, "Age": 50,
        })
        assert "probability" in result
        assert "risk_category" in result
        assert result["method"] == "full_ensemble"
        assert 0.0 <= result["probability"] <= 1.0
        assert result["risk_category"] in ("Low", "Medium", "High")

    def test_surrogate_prediction(self):
        from inference.predict_diabetes_risk import DiabetesRiskPredictor
        predictor = DiabetesRiskPredictor()
        predictor.load()

        result = predictor.predict({
            "Age": 50, "BMI": 33.6,
            "DiabetesPedigreeFunction": 0.627, "Pregnancies": 3,
        })
        assert "probability" in result
        assert 0.0 <= result["probability"] <= 1.0

    def test_low_risk_user(self):
        from inference.predict_diabetes_risk import DiabetesRiskPredictor
        predictor = DiabetesRiskPredictor()
        predictor.load()

        result = predictor.predict({
            "Pregnancies": 0, "Glucose": 80, "BloodPressure": 70,
            "SkinThickness": 20, "Insulin": 80, "BMI": 22.0,
            "DiabetesPedigreeFunction": 0.2, "Age": 25,
        })
        assert result["probability"] < 0.5

    def test_high_risk_user(self):
        from inference.predict_diabetes_risk import DiabetesRiskPredictor
        predictor = DiabetesRiskPredictor()
        predictor.load()

        result = predictor.predict({
            "Pregnancies": 8, "Glucose": 190, "BloodPressure": 90,
            "SkinThickness": 40, "Insulin": 300, "BMI": 40.0,
            "DiabetesPedigreeFunction": 1.2, "Age": 60,
        })
        assert result["probability"] > 0.4


# ═════════════════════════════════════════════════════════════════════
#  Model 2: User Embedding & Clustering
# ═════════════════════════════════════════════════════════════════════

class TestUserEmbeddingModel:
    """Unit tests for UserAutoencoder and UserClusterModel."""

    def test_autoencoder_forward(self):
        from models.user_embedding import UserAutoencoder
        model = UserAutoencoder(input_dim=USER_FEATURE_DIM, hidden_dim=64, embedding_dim=EMBEDDING_DIM)
        x = torch.randn(16, USER_FEATURE_DIM)
        reconstruction, embedding = model(x)

        assert reconstruction.shape == (16, USER_FEATURE_DIM)
        assert embedding.shape == (16, EMBEDDING_DIM)

    def test_autoencoder_encode(self):
        from models.user_embedding import UserAutoencoder
        model = UserAutoencoder(input_dim=USER_FEATURE_DIM, hidden_dim=64, embedding_dim=EMBEDDING_DIM)
        x = torch.randn(8, USER_FEATURE_DIM)
        emb = model.encode(x)
        assert emb.shape == (8, EMBEDDING_DIM)

    def test_cluster_model_fit_predict(self):
        from models.user_embedding import UserClusterModel
        embeddings = np.random.randn(100, EMBEDDING_DIM).astype(np.float32)
        cluster = UserClusterModel(n_clusters=5)
        cluster.fit(embeddings)
        assert cluster._fitted

        labels = cluster.predict(embeddings)
        assert labels.shape == (100,)
        assert set(np.unique(labels)).issubset(set(range(5)))

    def test_cluster_silhouette(self):
        from models.user_embedding import UserClusterModel
        embeddings = np.random.randn(200, EMBEDDING_DIM).astype(np.float32)
        cluster = UserClusterModel(n_clusters=5)
        cluster.fit(embeddings)
        score = cluster.score(embeddings)
        assert -1.0 <= score <= 1.0

    def test_cluster_profiles(self):
        from models.user_embedding import UserClusterModel
        cluster = UserClusterModel(n_clusters=3)
        cluster.set_cluster_profile(0, {"workout_split": "full_body"})
        assert cluster.get_cluster_profile(0) == {"workout_split": "full_body"}
        assert cluster.get_cluster_profile(99) == {}


class TestUserEmbeddingInference:
    """Integration tests for UserEmbeddingPredictor."""

    @pytest.fixture(autouse=True)
    def check_models(self):
        if not (SAVED_MODELS_DIR / "user_autoencoder.pt").exists():
            pytest.skip("User embedding model not trained yet")

    def test_embed_single(self):
        from inference.compute_user_embedding import UserEmbeddingPredictor
        predictor = UserEmbeddingPredictor()
        predictor.load()

        features = np.random.randn(USER_FEATURE_DIM).astype(np.float32)
        emb = predictor.embed(features)
        assert emb.shape == (EMBEDDING_DIM,)

    def test_embed_batch(self):
        from inference.compute_user_embedding import UserEmbeddingPredictor
        predictor = UserEmbeddingPredictor()
        predictor.load()

        features = np.random.randn(10, USER_FEATURE_DIM).astype(np.float32)
        embs = predictor.embed(features)
        assert embs.shape == (10, EMBEDDING_DIM)

    def test_assign_cluster(self):
        from inference.compute_user_embedding import UserEmbeddingPredictor
        predictor = UserEmbeddingPredictor()
        predictor.load()

        features = np.random.randn(USER_FEATURE_DIM).astype(np.float32)
        emb = predictor.embed(features)
        result = predictor.assign_cluster(emb)

        assert "cluster_id" in result
        assert "archetype" in result
        assert "plan_template" in result
        assert isinstance(result["cluster_id"], (int, np.integer))

    def test_end_to_end_predict(self):
        from inference.compute_user_embedding import UserEmbeddingPredictor
        predictor = UserEmbeddingPredictor()
        predictor.load()

        features = np.random.randn(USER_FEATURE_DIM).astype(np.float32)
        result = predictor.predict(features)

        assert "cluster_id" in result
        assert "embedding" in result
        assert "plan_template" in result
        assert len(result["embedding"]) == EMBEDDING_DIM


# ═════════════════════════════════════════════════════════════════════
#  Model 3: Exercise Recommender
# ═════════════════════════════════════════════════════════════════════

class TestExerciseRecommenderModel:
    """Unit tests for ExerciseRecommender."""

    def test_fit_and_score(self):
        from models.exercise_recommender import ExerciseRecommender
        model = ExerciseRecommender(EXERCISE_XGB_PARAMS)
        n_features = EMBEDDING_DIM + 21 + 4  # user embed + exercise feats + pair feats
        X = np.random.rand(300, n_features)
        y = np.random.randint(0, 2, 300)
        model.fit(X, y, verbose=False)
        assert model._fitted

        scores = model.score(X[:10])
        assert scores.shape == (10,)
        assert np.all((scores >= 0) & (scores <= 1))

    def test_rule_filter_equipment(self):
        from models.exercise_recommender import ExerciseRecommender
        exercises = pd.DataFrame({
            "name": ["Bench Press", "Push Up", "Lat Pulldown"],
            "equipment": ["Barbell", "None", "Machine"],
            "difficulty": [2, 1, 2],
            "injury_risk": [0.3, 0.1, 0.2],
            "cardio_intensity": [0.0, 0.0, 0.0],
        })
        user = {"conditions": [], "equipment_available": ["None"], "fitness_level": 3}
        valid = ExerciseRecommender.rule_filter(exercises, user)
        assert 1 in valid  # Push Up (no equipment)
        assert 0 not in valid  # Bench Press needs Barbell

    def test_rule_filter_conditions(self):
        from models.exercise_recommender import ExerciseRecommender
        exercises = pd.DataFrame({
            "name": ["Heavy Overhead Press", "Walking", "Sprint HIIT"],
            "equipment": ["None", "None", "None"],
            "difficulty": [3, 1, 3],
            "injury_risk": [0.5, 0.1, 0.4],
            "cardio_intensity": [0.2, 0.1, 0.9],
        })
        user = {"conditions": ["hypertension"], "equipment_available": ["None"], "fitness_level": 3}
        valid = ExerciseRecommender.rule_filter(exercises, user)
        assert 0 not in valid  # "heavy" + hypertension blocked
        assert 1 in valid  # Walking is fine

    def test_rule_filter_injury_recovery(self):
        from models.exercise_recommender import ExerciseRecommender
        exercises = pd.DataFrame({
            "name": ["Deadlift", "Chair Stretch"],
            "equipment": ["None", "None"],
            "difficulty": [3, 1],
            "injury_risk": [0.7, 0.1],
            "cardio_intensity": [0.0, 0.0],
        })
        user = {"conditions": ["injury_recovery"], "equipment_available": ["None"], "fitness_level": 2}
        valid = ExerciseRecommender.rule_filter(exercises, user)
        assert 0 not in valid  # High injury risk blocked
        assert 1 in valid  # Low risk ok

    def test_assemble_workout_diversity(self):
        from models.exercise_recommender import ExerciseRecommender
        scored = [
            {"exercise_id": i, "name": f"Ex{i}", "body_part": bp, "type": "Strength", "score": 1.0 - i * 0.01}
            for i, bp in enumerate(["Chest", "Chest", "Chest", "Legs", "Back", "Shoulders", "Arms", "Legs"])
        ]
        user = {"exercises_per_workout": 6}
        workout = ExerciseRecommender.assemble_workout(scored, user)
        assert len(workout) == 6
        body_parts = [e["body_part"] for e in workout]
        assert body_parts.count("Chest") <= 2  # max 2 per body part


# ═════════════════════════════════════════════════════════════════════
#  Model 4: Food Recommender & Meal Planner
# ═════════════════════════════════════════════════════════════════════

class TestFoodScorerModel:
    """Unit tests for FoodScorer."""

    def test_health_score_range(self):
        from models.food_recommender import FoodScorer
        scorer = FoodScorer(health_weight=0.6)
        food = {"calories": 200, "sodium_mg": 100, "sugar_g": 5, "fiber_g": 5}
        budget = {"calories": 800, "sodium_mg": 2300, "sugar_g": 50}
        constraints = {}
        score = scorer.health_score(food, constraints, budget)
        assert 0.0 <= score <= 1.0

    def test_health_score_penalizes_high_sodium(self):
        from models.food_recommender import FoodScorer
        scorer = FoodScorer()
        low_sodium = {"calories": 200, "sodium_mg": 100, "sugar_g": 5}
        high_sodium = {"calories": 200, "sodium_mg": 1500, "sugar_g": 5}
        budget = {"calories": 800, "sodium_mg": 2300, "sugar_g": 50}
        s_low = scorer.health_score(low_sodium, {}, budget)
        s_high = scorer.health_score(high_sodium, {}, budget)
        assert s_low > s_high

    def test_preference_score_cosine(self):
        from models.food_recommender import FoodScorer
        scorer = FoodScorer()
        food_emb = np.array([1, 0, 0, 0], dtype=np.float32)
        user_emb = np.array([1, 0, 0, 0], dtype=np.float32)
        score_same = scorer.preference_score(food_emb, user_emb)
        user_orth = np.array([0, 1, 0, 0], dtype=np.float32)
        score_orth = scorer.preference_score(food_emb, user_orth)
        assert score_same > score_orth

    def test_combined_score_range(self):
        from models.food_recommender import FoodScorer
        scorer = FoodScorer(health_weight=0.6)
        food = {"calories": 200, "sodium_mg": 100, "sugar_g": 5, "fiber_g": 5}
        food_emb = np.random.randn(8).astype(np.float32)
        user_emb = np.random.randn(8).astype(np.float32)
        budget = {"calories": 800, "sodium_mg": 2300, "sugar_g": 50}
        score = scorer.combined_score(food, food_emb, {}, user_emb, budget)
        assert 0.0 <= score <= 1.0


class TestMealPlannerModel:
    """Unit tests for MealPlanner ILP solver."""

    def test_plan_day_basic(self):
        from models.food_recommender import MealPlanner
        planner = MealPlanner()
        foods = pd.DataFrame({
            "food_id": range(20),
            "name": [f"Food_{i}" for i in range(20)],
            "calories": np.random.uniform(150, 500, 20),
            "protein_g": np.random.uniform(5, 30, 20),
            "carbs_g": np.random.uniform(10, 60, 20),
            "fat_g": np.random.uniform(2, 20, 20),
            "fiber_g": np.random.uniform(1, 10, 20),
            "sugar_g": np.random.uniform(1, 15, 20),
            "sodium_mg": np.random.uniform(50, 500, 20),
            "meal_type": ["breakfast"] * 5 + ["lunch"] * 5 + ["dinner"] * 5 + ["snack"] * 5,
        })
        scores = np.random.uniform(0.3, 1.0, 20)
        result = planner.plan_day(foods, scores, {}, calorie_target=2000, calorie_tolerance=500)

        assert "meals" in result
        assert "totals" in result
        assert result["status"] in ("optimal", "greedy_fallback")

    def test_plan_day_empty_foods(self):
        from models.food_recommender import MealPlanner
        planner = MealPlanner()
        empty = pd.DataFrame(columns=["food_id", "name", "calories", "meal_type"])
        result = planner.plan_day(empty, np.array([]), {}, calorie_target=2000)
        assert result["status"] == "no_candidates"


class TestUserTasteProfile:
    """Unit tests for UserTasteProfile."""

    def test_update_and_embedding(self):
        from models.food_recommender import UserTasteProfile
        profile = UserTasteProfile(embedding_dim=4)
        food_emb = np.array([1.0, 0.0, 0.5, 0.0], dtype=np.float32)
        profile.update(food_emb, liked=True)
        assert profile.n_updates == 1
        assert not np.allclose(profile.embedding, 0)

    def test_dislike_tracking(self):
        from models.food_recommender import UserTasteProfile
        profile = UserTasteProfile()
        profile.add_dislike(42)
        profile.add_dislike(99)
        assert 42 in profile.disliked_food_ids
        assert len(profile.disliked_food_ids) == 2

    def test_serialization_roundtrip(self):
        from models.food_recommender import UserTasteProfile
        profile = UserTasteProfile(embedding_dim=4)
        profile.update(np.random.randn(4).astype(np.float32))
        profile.update_cuisine("Indian")
        profile.add_dislike(7)

        data = profile.to_dict()
        restored = UserTasteProfile.from_dict(data, embedding_dim=4)
        assert np.allclose(profile.embedding, restored.embedding)
        assert restored.cuisine_counts == {"Indian": 1}
        assert 7 in restored.disliked_food_ids

    def test_preferred_cuisine(self):
        from models.food_recommender import UserTasteProfile
        profile = UserTasteProfile()
        for _ in range(5):
            profile.update_cuisine("Indian")
        for _ in range(3):
            profile.update_cuisine("American")
        assert profile.preferred_cuisine() == "Indian"


class TestMealPlanInference:
    """Integration tests for MealPlanPredictor."""

    @pytest.fixture(autouse=True)
    def check_data(self):
        if not (PROCESSED_DIR / "foods_clean.csv").exists():
            pytest.skip("Food data not preprocessed yet")

    def test_plan_healthy_user(self):
        from inference.plan_meals import MealPlanPredictor
        planner = MealPlanPredictor()
        planner.load()

        result = planner.plan_day({
            "conditions": [],
            "calorie_target": 2000,
            "dietary_prefs": [],
        })
        assert "meals" in result
        assert "totals" in result
        assert result["n_foods"] >= 1
        assert result["totals"].get("calories", 0) > 0

    def test_plan_diabetic_user(self):
        from inference.plan_meals import MealPlanPredictor
        planner = MealPlanPredictor()
        planner.load()

        result = planner.plan_day({
            "conditions": ["type2_diabetes"],
            "calorie_target": 1800,
            "dietary_prefs": [],
        })
        assert result["constraint_satisfaction"] is True or result["constraint_satisfaction"] is False
        assert result["n_foods"] >= 1

    def test_plan_multiple_conditions(self):
        from inference.plan_meals import MealPlanPredictor
        planner = MealPlanPredictor()
        planner.load()

        result = planner.plan_day({
            "conditions": ["type2_diabetes", "hypertension"],
            "calorie_target": 1800,
            "dietary_prefs": [],
        })
        assert "totals" in result


# ═════════════════════════════════════════════════════════════════════
#  Model 5: Stress Detection
# ═════════════════════════════════════════════════════════════════════

class TestStressModel:
    """Unit tests for StressDetector."""

    def test_heuristic_elevated_hr_at_rest(self):
        from models.stress_model import StressDetector
        detector = StressDetector(STRESS_RF_PARAMS, resting_hr=70.0)
        prob = detector.predict_heuristic(
            hr_mean=90, hr_std=10, steps_last_1h=100,
            time_since_activity_min=120, sleep_hours=5,
        )
        assert prob > 0.5  # elevated HR + poor sleep + sedentary

    def test_heuristic_calm_state(self):
        from models.stress_model import StressDetector
        detector = StressDetector(STRESS_RF_PARAMS, resting_hr=70.0)
        prob = detector.predict_heuristic(
            hr_mean=72, hr_std=4, steps_last_1h=2000,
            time_since_activity_min=30, sleep_hours=8,
        )
        assert prob < 0.3

    def test_ml_fit_and_predict(self):
        from models.stress_model import StressDetector
        detector = StressDetector(STRESS_RF_PARAMS)
        X = np.random.rand(200, 8)
        y = np.random.randint(0, 2, 200)
        detector.fit(X, y)
        assert detector._ml_fitted

        probs = detector.predict_proba_ml(X[:10])
        assert probs.shape == (10,)
        assert np.all((probs >= 0) & (probs <= 1))

    def test_predict_unified_ml(self):
        from models.stress_model import StressDetector
        detector = StressDetector(STRESS_RF_PARAMS)
        X = np.random.rand(100, 8)
        y = np.random.randint(0, 2, 100)
        detector.fit(X, y)

        result = detector.predict({
            "hr_features": np.random.rand(8),
            "hr_mean": 85, "hr_std": 8,
            "steps_last_1h": 500,
            "time_since_activity_min": 60,
            "sleep_hours": 7,
        })
        assert "probability" in result
        assert "is_stressed" in result
        assert result["method"] == "ml"

    def test_predict_unified_heuristic(self):
        from models.stress_model import StressDetector
        detector = StressDetector(STRESS_RF_PARAMS)
        # Not fitted, should fallback to heuristic
        result = detector.predict({
            "hr_mean": 95, "hr_std": 12,
            "steps_last_1h": 100,
            "time_since_activity_min": 120,
            "sleep_hours": 4,
        })
        assert result["method"] == "heuristic"
        assert result["probability"] > 0

    def test_interventions_when_stressed(self):
        from models.stress_model import StressDetector
        detector = StressDetector(STRESS_RF_PARAMS)
        result = detector.predict({
            "hr_mean": 100, "hr_std": 15,
            "steps_last_1h": 50,
            "time_since_activity_min": 120,
            "sleep_hours": 4,
        })
        if result["is_stressed"]:
            assert len(result["interventions"]) > 0
            assert "breathing_exercise_4_7_8" in result["interventions"]

    def test_calibration(self):
        from models.stress_model import StressDetector
        detector = StressDetector(STRESS_RF_PARAMS)
        X = np.random.rand(100, 8)
        y = np.random.randint(0, 2, 100)
        detector.fit(X, y)

        preds = detector.predict_proba_ml(X)
        detector.calibrate_with_self_reports(preds, y)
        assert detector._calibrated
        assert 0.2 <= detector.stress_threshold <= 0.8

    def test_update_resting_hr(self):
        from models.stress_model import StressDetector
        detector = StressDetector(STRESS_RF_PARAMS)
        detector.update_resting_hr(65.0)
        assert detector.resting_hr == 65.0


class TestStressInference:
    """Integration tests for StressPredictor."""

    @pytest.fixture(autouse=True)
    def check_models(self):
        if not (SAVED_MODELS_DIR / "stress_detector.joblib").exists():
            pytest.skip("Stress model not trained yet")

    def test_predict_with_hr(self):
        from inference.detect_stress import StressPredictor
        predictor = StressPredictor()
        predictor.load()

        result = predictor.predict({
            "hr_mean": 92.5, "hr_std": 12.3, "hr_max": 108.0,
            "hr_range": 15.5, "rmssd": 25.0, "signal_energy": 0.65,
            "zcr": 0.22, "peak_rate": 1.54,
            "steps_last_1h": 150,
            "time_since_activity_min": 95,
            "sleep_hours": 5.5,
        })
        assert "probability" in result
        assert "is_stressed" in result
        assert "method" in result
        assert 0.0 <= result["probability"] <= 1.0

    def test_predict_without_hr(self):
        from inference.detect_stress import StressPredictor
        predictor = StressPredictor()
        predictor.load()

        result = predictor.predict({
            "hr_mean": 85, "hr_std": 6,
            "steps_last_1h": 3000,
            "time_since_activity_min": 30,
            "sleep_hours": 7.5,
        })
        assert result["method"] == "heuristic"

    def test_batch_prediction(self):
        from inference.detect_stress import StressPredictor
        predictor = StressPredictor()
        predictor.load()

        X = np.random.rand(20, 8).astype(np.float32)
        probs = predictor.predict_batch(X)
        assert probs.shape == (20,)
        assert np.all((probs >= 0) & (probs <= 1))


# ═════════════════════════════════════════════════════════════════════
#  Cross-cutting: Utils & Config
# ═════════════════════════════════════════════════════════════════════

class TestUtils:
    """Tests for shared utility functions."""

    def test_ndcg_at_k(self):
        from utils import ndcg_at_k
        # Perfect ranking
        assert ndcg_at_k(np.array([1, 1, 1, 0, 0])) == pytest.approx(1.0)
        # All zeros
        assert ndcg_at_k(np.array([0, 0, 0])) == 0.0

    def test_hit_rate_at_k(self):
        from utils import hit_rate_at_k
        assert hit_rate_at_k(np.array([1, 2, 3, 4, 5]), {3}, k=5) == 1.0
        assert hit_rate_at_k(np.array([1, 2, 3, 4, 5]), {99}, k=5) == 0.0

    def test_normalize_array(self):
        from utils import normalize_array
        arr = np.array([0, 5, 10], dtype=np.float32)
        normed, mn, mx = normalize_array(arr)
        assert normed[0] == pytest.approx(0.0)
        assert normed[2] == pytest.approx(1.0)

    def test_set_seed_determinism(self):
        from utils import set_seed
        set_seed(42)
        a = np.random.rand(5)
        set_seed(42)
        b = np.random.rand(5)
        assert np.allclose(a, b)

    def test_config_paths_exist(self):
        assert SAVED_MODELS_DIR.exists()
        assert PROCESSED_DIR.exists()
