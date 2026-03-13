"""
FitGenix ML — User Embedding Model
Autoencoder for user representation + KMeans clustering.
"""
import numpy as np
import torch
import torch.nn as nn
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score


class UserAutoencoder(nn.Module):

    def __init__(self, input_dim: int, hidden_dim: int = 64, embedding_dim: int = 16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, embedding_dim),
        )
        self.decoder = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, input_dim),
            nn.Sigmoid(),  # outputs are normalized [0, 1]
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        embedding = self.encoder(x)
        reconstruction = self.decoder(embedding)
        return reconstruction, embedding

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        self.eval()
        with torch.no_grad():
            return self.encoder(x)


class UserClusterModel:
    """
    KMeans clustering on top of autoencoder embeddings.
    Maps cluster IDs to plan templates.
    """

    def __init__(self, n_clusters: int = 8, random_state: int = 42):
        self.kmeans = MiniBatchKMeans(
            n_clusters=n_clusters,
            random_state=random_state,
            batch_size=256,
        )
        self.n_clusters = n_clusters
        self._fitted = False
        self.cluster_profiles: dict[int, dict] = {}

    def fit(self, embeddings: np.ndarray):
        self.kmeans.fit(embeddings)
        self._fitted = True

    def predict(self, embeddings: np.ndarray) -> np.ndarray:
        assert self._fitted, "ClusterModel not fitted"
        return self.kmeans.predict(embeddings)

    def score(self, embeddings: np.ndarray) -> float:
        """Silhouette score for clustering quality."""
        labels = self.predict(embeddings)
        if len(set(labels)) < 2:
            return 0.0
        return silhouette_score(embeddings, labels, sample_size=min(5000, len(embeddings)))

    def set_cluster_profile(self, cluster_id: int, profile: dict):
        """Map a cluster to a plan template description."""
        self.cluster_profiles[cluster_id] = profile

    def get_cluster_profile(self, cluster_id: int) -> dict:
        return self.cluster_profiles.get(cluster_id, {})


# ── Plan template definitions per cluster archetype ──────────────────

CLUSTER_PLAN_TEMPLATES = {
    "healthy_active_young": {
        "workout_split": "push_pull_legs",
        "workout_days": 5,
        "cardio_days": 2,
        "calorie_surplus": 200,
        "protein_g_per_kg": 1.8,
        "lifestyle": ["active_recovery", "mobility_work"],
    },
    "healthy_sedentary": {
        "workout_split": "full_body_3x",
        "workout_days": 3,
        "cardio_days": 3,
        "calorie_deficit": 300,
        "protein_g_per_kg": 1.4,
        "lifestyle": ["walk_breaks_hourly", "standing_desk"],
    },
    "overweight_beginner": {
        "workout_split": "full_body_3x",
        "workout_days": 3,
        "cardio_days": 4,
        "calorie_deficit": 500,
        "protein_g_per_kg": 1.2,
        "lifestyle": ["walk_10k_steps", "sleep_hygiene"],
    },
    "diabetic_patient": {
        "workout_split": "upper_lower",
        "workout_days": 4,
        "cardio_days": 3,
        "calorie_adjustment": 0,
        "protein_g_per_kg": 1.2,
        "lifestyle": ["post_meal_walk_15min", "glucose_logging"],
        "diet_rules": ["low_gi", "high_fiber"],
    },
    "hypertensive_senior": {
        "workout_split": "full_body_2x",
        "workout_days": 2,
        "cardio_days": 5,
        "calorie_adjustment": 0,
        "protein_g_per_kg": 1.0,
        "lifestyle": ["blood_pressure_logging", "stress_management"],
        "diet_rules": ["low_sodium", "dash_diet"],
        "exercise_cautions": ["avoid_heavy_overhead", "avoid_valsalva"],
    },
    "stressed_office_worker": {
        "workout_split": "full_body_3x",
        "workout_days": 3,
        "cardio_days": 2,
        "calorie_adjustment": -200,
        "protein_g_per_kg": 1.4,
        "lifestyle": ["breathing_exercises_3x_daily", "screen_breaks", "sleep_hygiene"],
    },
    "athletic_intermediate": {
        "workout_split": "push_pull_legs",
        "workout_days": 5,
        "cardio_days": 2,
        "calorie_surplus": 300,
        "protein_g_per_kg": 2.0,
        "lifestyle": ["periodization", "deload_week_every_4"],
    },
    "post_injury_recovery": {
        "workout_split": "rehab_focused",
        "workout_days": 3,
        "cardio_days": 2,
        "calorie_adjustment": 0,
        "protein_g_per_kg": 1.4,
        "lifestyle": ["pain_logging", "physio_exercises"],
        "exercise_cautions": ["avoid_injured_area", "low_impact_only"],
    },
}
