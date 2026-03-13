
┌────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                │
│  Google Fit API  │  Onboarding Survey  │  Manual Logs (optional)   │
└────────┬─────────────────┬──────────────────────┬──────────────────┘
         │                 │                      │
         ▼                 ▼                      ▼
┌────────────────────────────────────────────────────────────────────┐
│                    FEATURE STORE (SQLite)                           │
│  user_profiles │ activity_daily │ meal_logs │ feedback │ vitals    │
└────────┬───────────────────────────────────────────────────────────┘
         │
    ┌────┴────────────────────────────────────────┐
    ▼            ▼           ▼          ▼         ▼
┌────────┐ ┌─────────┐ ┌────────┐ ┌────────┐ ┌───────┐
│Model 1 │ │Model 2  │ │Model 3 │ │Model 4 │ │Model 5│
│Diabetes│ │User Emb │ │Exercise│ │Food/   │ │Stress │
│Risk    │ │Cluster  │ │Recomm. │ │Diet    │ │Detect │
└───┬────┘ └────┬────┘ └───┬────┘ └───┬────┘ └──┬────┘
    │           │          │          │          │
    ▼           ▼          ▼          ▼          ▼
┌────────────────────────────────────────────────────────────────────┐
│              PERSONALIZATION ENGINE (FastAPI)                       │
│  Combines all model outputs → daily plan → adapts over time        │
└────────────────────────────────────────────────────────────────────┘
```

### Model Summary

| # | Model | Task | Algorithm | Input | Output |
|---|-------|------|-----------|-------|--------|
| 1 | Diabetes Risk | Binary classification | XGBoost + Logistic Regression (ensemble) | User profile + Fit aggregates | Risk probability [0,1] + category |
| 2 | User Embedding | Unsupervised embedding | PCA/Autoencoder + KMeans | Demographics + behavior + goals | 16-dim vector + cluster ID |
| 3 | Exercise Recommender | Learning-to-rank | GBT ranker (XGBoost) | User embed + exercise features | Score per exercise |
| 4 | Food/Diet Recommender | Constrained optimization | Scoring model + ILP solver | User health profile + food features | Daily meal plan |
| 5 | Stress Detection | Binary classification | Random Forest / shallow MLP | HR stats + activity context | Stress probability |

### Device Support
- All models designed for **CPU inference** (< 100ms per call)
- Training supports **CUDA** when available (auto-detected)
- Model sizes: all < 50MB combined (suitable for free-tier hosting)

---

## 2. Model 1: Diabetes Risk

### Dataset
- **Pima Indians Diabetes** (`datasets/diabetes.csv`)
- 768 samples, 8 features, binary outcome

### Features & Preprocessing
| Feature | Pima Column | FitGenix Mapping | Preprocessing |
|---------|-------------|------------------|---------------|
| Pregnancies | Pregnancies | From survey | Clip [0, 20] |
| Glucose | Glucose | *Not available* → impute from risk proxy | Median impute zeros |
| BloodPressure | BloodPressure | *Optional manual entry* or median | Median impute zeros |
| SkinThickness | SkinThickness | *Not available* → median impute | Median impute zeros |
| Insulin | Insulin | *Not available* → median impute | Median impute zeros |
| BMI | BMI | Computed: weight/(height_m²) | Direct compute |
| DiabetesPedigree | DiabetesPedigreeFunction | Family history score (proxy) | Scale [0, 2.5] |
| Age | Age | From survey | Clip [21, 81] |

**Zero-imputation strategy**: Pima dataset uses 0 for missing values in Glucose, BP, SkinThickness, Insulin, BMI. We replace 0s with column medians.

**Feature engineering additions**:
- `BMI_Age_interaction` = BMI × Age / 100
- `Glucose_BMI_ratio` = Glucose / BMI (where available)

### Model Choice
1. **Primary**: XGBoost classifier (handles missing values natively, strong on tabular data)
2. **Calibrated**: Logistic Regression with Platt scaling for well-calibrated probabilities
3. **Ensemble**: Average predicted probabilities from both

### Training Pipeline
- 80/20 stratified train/test split
- 5-fold stratified cross-validation on train set
- Hyperparameter tuning via Optuna (30 trials)
- Metrics: **AUC-ROC** (primary), accuracy, precision, recall, F1, Brier score
- Save: model artifacts + feature scaler + imputer + threshold

### Production Adaptation (Surrogate Model)
Since real FitGenix users won't have lab values (Glucose, Insulin, SkinThickness):
1. Train the full model on Pima with all 8 features
2. Train a **surrogate model** on only the features we CAN get: Age, BMI, family history proxy, activity level
3. The surrogate uses the full model's predictions as soft labels (knowledge distillation)
4. At inference, use surrogate for users without lab data; full model for users who enter lab values

### Inference
- **Input**: user_profile (age, bmi, family_history, activity_minutes_weekly, optional: glucose, bp)
- **Output**: `{ risk_probability: 0.72, risk_category: "High", contributing_factors: [...] }`
- **Frequency**: Recompute weekly or on profile update

---

## 3. Model 2: User Embedding & Clustering

### Feature Definition (Raw User Vector — 28 dimensions)

**Demographics (5)**:
- age (normalized)
- sex (0/1)
- bmi (normalized)
- num_conditions (count of diseases: diabetes, HTN, asthma, etc.)
- fitness_level (1=sedentary, 2=light, 3=moderate, 4=active, 5=very_active)

**Goals & Preferences (8)**:
- goal_weight_loss (0/1)
- goal_muscle_gain (0/1)
- goal_endurance (0/1)
- goal_flexibility (0/1)
- goal_disease_management (0/1)
- diet_type (one-hot: omnivore/vegetarian/vegan/keto → 3 dims)
- available_time_minutes (normalized)
- equipment_level (0=none, 1=basic, 2=full_gym)

**Behavior (rolling 14-day averages, 15)**:
- avg_daily_steps (normalized)
- avg_active_minutes
- avg_heart_rate
- hr_variability_proxy (std of HR readings)
- workout_count_per_week
- workout_completion_rate
- avg_workout_duration
- sleep_hours_avg
- sleep_consistency (std of bedtime)
- diet_adherence_rate
- calorie_deviation_pct (actual vs target)
- stress_score_avg
- pain_score_avg
- mood_score_avg
- days_since_last_workout

### Dimensionality Reduction
**Option A — PCA**: Reduce 28-dim → 16-dim (retain ~90% variance)
**Option B — Autoencoder** (preferred for nonlinearity):
- Architecture: 28 → 64 → 16 → 64 → 28
- Activation: ReLU (hidden), Sigmoid (output for normalized inputs)
- Loss: MSE reconstruction
- Train on synthetic user pool (10,000 users)
- Embedding = 16-dim bottleneck layer

### Clustering
- **Algorithm**: MiniBatchKMeans (scalable)
- **Choosing k**: Silhouette score + elbow method on k ∈ [4, 15]
- **Expected clusters** (~8):
  - Healthy active young, Healthy sedentary, Overweight beginner, Diabetic patient,
  - Hypertensive senior, Stressed office worker, Athletic intermediate, Post-injury recovery

### Usage
- Each cluster maps to a **plan template** (baseline workout split, diet pattern, lifestyle rules)
- New users get cluster assignment instantly from onboarding survey
- After 7 days of data, embedding is recomputed with behavioral features
- Clusters are re-fitted monthly on growing user base

---

## 4. Model 3: Exercise Recommender

### Exercise Feature Vector (per exercise, 18 dims)
From `megaGymDataset.csv` + Open Exercise DB:

| Feature | Type | Source |
|---------|------|--------|
| exercise_id | int | DB primary key |
| type | one-hot (3) | Strength / Cardio / Flexibility |
| body_part | one-hot (8) | Chest, Back, Legs, Arms, Shoulders, Abs, Full Body, Other |
| equipment | one-hot (5) | None, Bands, Barbell, Dumbbell, Machine |
| difficulty | ordinal [1-3] | Beginner/Intermediate/Expert |
| is_compound | binary | Multi-joint movement? |
| cardio_intensity | float [0-1] | Estimated MET / max MET |
| injury_risk | float [0-1] | Heuristic from exercise type |
| rating | float | From dataset (normalized) |

### User Features for Exercise Scoring
- User embedding (16-dim from Model 2)
- User fitness level
- Equipment available
- Recent exercise history (last 7 days: body parts trained as vector)
- Current stress level (from Model 5)
- Conditions (contraindication flags)

### Ranking Model
**XGBoost ranker** (pairwise ranking) predicting P(completion & satisfaction):

**Input features** (per user-exercise pair):
- user_embedding (16)
- exercise_features (18)
- similarity_score: cosine(user_preferred_exercises_avg_embed, exercise_embed)
- difficulty_gap: exercise_difficulty - user_fitness_level
- body_part_staleness: days since last trained this body part
- equipment_match: 1 if user has equipment, 0 otherwise

**Label**: 1 = completed + not disliked, 0 = skipped/abandoned/disliked

### Synthetic Training Data Generation
1. Generate 500 synthetic users with varied profiles
2. For each user, simulate 90 days of workout logs
3. Per day: present 20 candidate exercises, user "completes" 4-6 based on:
   - Higher completion if difficulty matches fitness ±1
   - Higher completion if equipment is available
   - Higher completion for preferred body parts
   - Lower completion on high-stress days
   - Noise factor for exploration
4. Creates ~2.7M interaction records

### Training
- 80/10/10 train/val/test split (by user, not by row)
- Metrics: AUC, NDCG@10, Hit Rate@5
- Train XGBoost with `rank:pairwise` objective

### Inference Pipeline (per user, per day)
1. **Candidate generation**: Filter exercises by equipment + contraindications + rule-based safety
2. **Score computation**: Run ranker on each (user, exercise) pair
3. **Workout assembly**:
   - Select top-K exercises ensuring body part diversity
   - Apply workout structure: warm-up → main exercises → cooldown
   - Enforce variety: no more than 2 exercises for same body part
   - Apply progression: if completion rate > 90% for 2 weeks, bump difficulty
4. **Exploration**: With 10% probability, inject one random exercise from pool (contextual bandit ε-greedy)

---

## 5. Model 4: Food/Diet Recommender

### Food Feature Vector (per food/recipe, 20+ dims)
From USDA FoodData Central (`datasets/FoodData_Central_csv_2025-12-18/`) + IFCT2017 (`ifct2017_compositions.csv`):

| Feature | Unit | Description |
|---------|------|-------------|
| calories | kcal | Per serving |
| protein_g | g | Protein content |
| carbs_g | g | Total carbohydrates |
| fat_g | g | Total fat |
| fiber_g | g | Dietary fiber |
| sugar_g | g | Total sugars |
| sodium_mg | mg | Sodium |
| sat_fat_g | g | Saturated fat |
| cholesterol_mg | mg | Cholesterol |
| potassium_mg | mg | Potassium |
| glycemic_index | int | Estimated GI category (low/med/high) |
| cuisine | one-hot (4) | Indian / American / Mediterranean / Other |
| meal_type | one-hot (4) | Breakfast / Lunch / Dinner / Snack |
| diet_tags | multi-hot (6) | vegetarian, vegan, low_gi, low_sodium, diabetic_friendly, heart_healthy |
| food_category | embedding (4) | Learned from category hierarchy |

### User Taste/Health Profile (per user)
- **Health constraints** (from conditions): calorie_target, max_sodium, max_sugar, max_sat_fat, min_fiber, min_protein, gi_preference
- **Taste profile** (learned): running average of food embeddings actually consumed (16-dim)
- **Cuisine preference weights**: [Indian, American, Mediterranean, Other]
- **Disliked foods**: explicit exclusion set

### Scoring Model

**Health Score** (rule-based, per food):
```
health_score = (
    w1 * nutrient_fit(food, user_constraints) +  # How well macros fit remaining daily budget
    w2 * disease_bonus(food, user_conditions) +   # Bonus for diabetic-friendly if user is diabetic
    w3 * penalty(food, user_constraints)           # Penalty for exceeding sodium/sugar limits
)
```

**Preference Score** (ML-based):
```
preference_score = cosine_similarity(user_taste_embedding, food_embedding) +
                   cuisine_match_bonus +
                   past_consumption_frequency_bonus
```

**Combined Score**: `α * health_score + (1-α) * preference_score` where α=0.6 (health-first)

### Meal Plan Assembly (Constrained Optimization)

Using **PuLP** (Python ILP solver):

**Decision variables**: x[f,m] ∈ {0,1} — food f assigned to meal slot m

**Objective**: Maximize Σ combined_score(f) × x[f,m]

**Constraints**:
- Σ calories(f) × x[f,m] ∈ [target - 100, target + 100]
- Σ protein(f) × x[f,m] ≥ min_protein
- Σ sodium(f) × x[f,m] ≤ max_sodium
- Σ sugar(f) × x[f,m] ≤ max_sugar
- Each meal slot gets 1-3 items
- No repeated foods in same day
- At least one item per meal type

### Training & Adaptation
1. **Food embeddings**: PCA on nutrition feature matrix (→ 8-dim) + category encoding (→ 4-dim) = 12-dim food embedding
2. **Taste profile update**: After each meal log, exponential moving average:
   `taste_embed = 0.9 * taste_embed + 0.1 * consumed_food_embed`
3. **Evaluation**: On synthetic logs — Hit Rate@5, NDCG@5, constraint satisfaction rate
4. **Disease-specific rules** (hard-coded from medical literature):
   - T2D: GI < 55, sugar < 25g/day, fiber > 30g/day
   - HTN: sodium < 1500mg, potassium > 3500mg, DASH diet pattern
   - Obesity: calorie deficit 500 kcal, protein > 1.2g/kg
   - Fatty liver: sat_fat < 10% calories, no alcohol, high fiber

---

## 6. Model 5: Stress Detection

### Feature Set (inspired by WESAD, adapted for Google Fit)

From WESAD we know HR-based features predict stress well. Our Google Fit features:

| Feature | Description | Derivation |
|---------|-------------|------------|
| hr_mean_1h | Mean HR last 1 hour | Google Fit HR stream |
| hr_std_1h | HR variability last 1 hour | Std of HR readings |
| hr_max_1h | Peak HR last 1 hour | Max reading |
| hr_resting_delta | Current HR - resting HR | Deviation from baseline |
| rmssd_proxy | Approx HRV (if RR intervals available) | √mean(ΔRR²) |
| steps_last_1h | Steps in last hour | Context: active or sedentary? |
| time_since_last_activity | Minutes since last >100 steps/5min | Sedentary duration |
| time_of_day | Hour (normalized) | Circadian context |
| sleep_hours_last_night | Previous night sleep | Recovery context |
| recent_self_report | Last stress self-report | Calibration anchor |

### Model
**Primary**: Random Forest (100 trees) trained on WESAD HR features
**Fallback**: Rule-based heuristic when HR data is insufficient:
```
if hr_resting_delta > 15 AND steps_last_1h < 100 AND time_since_last_activity > 60:
    stress_likely = True
```

### Training on WESAD
1. Extract HR-derived features from RespiBAN sensor data (700Hz → downsample)
2. Labels: Baseline=0, Stress(TSST)=1, Meditation=0, Amusement=0
3. Train RF on 15 subjects, LOSO cross-validation
4. Expected AUC: ~0.85 on HR-only features

### Domain Transfer to Google Fit
- Google Fit HR is sparse (maybe every few minutes, not continuous)
- **Calibration strategy**: Use first 2 weeks of user self-reports (3x daily stress check-ins) to calibrate thresholds
- **Hybrid approach**: Start with heuristic rules, switch to ML model after 50+ self-reports

### Usage
- Trigger: breathing exercise suggestion, walk break, intensity reduction
- Log stress episodes for Model 2 (user embedding) and Model 3 (workout intensity adjustment)

---

## 7. Personalization Loop

```
Day 1-7:    Cluster-based defaults (survey only)
             → User gets template plan from nearest cluster

Day 7-14:   Behavioral embedding begins updating
             → Google Fit data + initial feedback → refine embedding
             → Model 3 & 4 start using real preference signals

Day 14-30:  Full personalization active
             → Exercise ranker uses 2 weeks of completion data
             → Diet scorer uses meal log patterns
             → Stress model calibrated with self-reports

Day 30+:    Continuous adaptation
             → Weekly embedding recompute
             → Monthly cluster re-evaluation
             → Progression: difficulty auto-adjusts
             → Diabetes risk recomputed monthly
```

### Feedback Signals
| Signal | Source | Used By |
|--------|--------|---------|
| Exercise completion | App tracking | Model 3 |
| Exercise rating (1-5) | User input | Model 3 |
| Meal consumed vs planned | Meal log | Model 4 |
| Food liked/disliked | User input | Model 4 |
| Stress self-report | 3x daily prompt | Model 5 |
| Weight update | Weekly manual | Model 1, 2 |
| Sleep quality | Google Fit | Model 2, 5 |
| Pain/symptom log | Optional input | Model 2, 3 |

---

## 8. Practical Training Setup

### Code Organization
```
ml/
├── config.py                 # All hyperparameters, paths, feature definitions
├── utils.py                  # Common utilities (device selection, saving, loading)
├── data/
│   ├── preprocess_diabetes.py
│   ├── preprocess_wesad.py
│   ├── preprocess_food.py
│   ├── preprocess_exercises.py
│   └── synthetic_generator.py    # Generate synthetic users, logs, feedback
├── models/
│   ├── diabetes_model.py         # Model 1 definition
│   ├── user_embedding.py         # Model 2 (autoencoder + clustering)
│   ├── exercise_recommender.py   # Model 3 (XGBoost ranker)
│   ├── food_recommender.py       # Model 4 (scorer + ILP planner)
│   └── stress_model.py           # Model 5 definition
├── training/
│   ├── train_diabetes.py
│   ├── train_user_embedding.py
│   ├── train_exercise_recommender.py
│   ├── train_food_recommender.py
│   └── train_stress.py
├── inference/
│   ├── predict_diabetes_risk.py
│   ├── compute_user_embedding.py
│   ├── recommend_exercises.py
│   ├── plan_meals.py
│   └── detect_stress.py
├── evaluation/
│   ├── evaluate_all.py
│   └── metrics.py
└── saved_models/              # .joblib / .pt / .json artifacts
```

### Training Order
1. `preprocess_*.py` scripts first (ETL)
2. `synthetic_generator.py` to create mock user data
3. `train_diabetes.py` (independent, uses Pima dataset)
4. `train_stress.py` (independent, uses WESAD)
5. `train_user_embedding.py` (uses synthetic user profiles)
6. `train_exercise_recommender.py` (uses synthetic interaction logs)
7. `train_food_recommender.py` (uses food DB + synthetic meal logs)

### Model Persistence
- scikit-learn / XGBoost: `joblib.dump()` / `joblib.load()`
- PyTorch (autoencoder): `torch.save(model.state_dict(), path)`
- Feature scalers & encoders: saved alongside models as `.joblib`
- All saved to `ml/saved_models/`

---

## 9. Evaluation Plan

### Offline Metrics

| Model | Primary Metric | Secondary | Target |
|-------|---------------|-----------|--------|
| Diabetes Risk | AUC-ROC | Brier Score, F1 | >0.82 AUC |
| User Embedding | Silhouette Score | Cluster purity | >0.35 silhouette |
| Exercise Recommender | NDCG@10 | Hit Rate@5, AUC | >0.75 NDCG |
| Food Recommender | Constraint Satisfaction % | NDCG@5, Diversity | >95% constraint sat |
| Stress Detection | AUC-ROC | Accuracy, F1 | >0.80 AUC |

### Synthetic Experiments
1. **Personalization quality**: Compare recommendations for 10 user archetypes — verify differentiation
2. **Adaptation speed**: Simulate 30 days of feedback, measure metric improvement over time
3. **Constraint satisfaction**: Verify 100% of meal plans meet hard health constraints
4. **Cold-start handling**: Measure quality at day 1 (cluster-only) vs day 14 (personalized)
5. **A/B simulation**: Random recommendations vs model recommendations — measure engagement proxy

---

## 10. Deployment & Free-Tier Optimization

- **Docker**: `python:3.11-slim` base, models copied in
- **Total model size**: ~30MB (XGBoost ~5MB each, autoencoder ~1MB, food index ~10MB)
- **RAM**: < 256MB at runtime
- **Inference time**: < 100ms per recommendation call
- **SQLite** for user data + food/exercise indices
- **Background jobs**: Weekly re-embedding, monthly risk recompute
- **ONNX export** option for further optimization
