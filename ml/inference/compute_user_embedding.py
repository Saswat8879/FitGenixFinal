"""
FitGenix ML — Inference: User Embedding & Cluster Assignment
Loads autoencoder + cluster model to embed new users and return plan templates.
"""
import sys, os
import numpy as np
import torch
import joblib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    SAVED_MODELS_DIR, PROCESSED_DIR, EMBEDDING_DIM,
    AUTOENCODER_PARAMS, USER_FEATURE_DIM,
)
from utils import load_torch_model, load_sklearn_model, get_device, logger
from models.user_embedding import UserAutoencoder, UserClusterModel, CLUSTER_PLAN_TEMPLATES


class UserEmbeddingPredictor:
    """Production inference wrapper for user embedding + clustering."""

    def __init__(self):
        self.autoencoder = None
        self.cluster_model = None
        self.scaler = None
        self.device = get_device()
        self._loaded = False

    def load(self):
        """Load autoencoder, cluster model, and scaler."""
        self.autoencoder = UserAutoencoder(
            input_dim=USER_FEATURE_DIM,
            hidden_dim=AUTOENCODER_PARAMS["hidden_dim"],
            embedding_dim=AUTOENCODER_PARAMS["embedding_dim"],
        )
        load_torch_model(self.autoencoder, "user_autoencoder", SAVED_MODELS_DIR)
        self.autoencoder.to(self.device)
        self.autoencoder.eval()

        self.cluster_model = load_sklearn_model("user_cluster_model", SAVED_MODELS_DIR)
        self.scaler = joblib.load(PROCESSED_DIR / "user_feature_scaler.joblib")
        self._loaded = True
        logger.info("UserEmbeddingPredictor loaded.")

    def embed(self, user_features: np.ndarray) -> np.ndarray:
        """
        Compute 16-dim embedding for one or more users.

        user_features: (n_users, 30) or (30,)
        Returns: (n_users, 16) or (16,)
        """
        if not self._loaded:
            self.load()

        single = user_features.ndim == 1
        if single:
            user_features = user_features.reshape(1, -1)

        # Pad or truncate to expected dim
        if user_features.shape[1] < USER_FEATURE_DIM:
            pad = np.zeros((user_features.shape[0], USER_FEATURE_DIM - user_features.shape[1]))
            user_features = np.hstack([user_features, pad])
        elif user_features.shape[1] > USER_FEATURE_DIM:
            user_features = user_features[:, :USER_FEATURE_DIM]

        x_scaled = self.scaler.transform(user_features).astype(np.float32)
        x_tensor = torch.from_numpy(x_scaled).to(self.device)

        with torch.no_grad():
            embedding = self.autoencoder.encode(x_tensor)

        result = embedding.cpu().numpy()
        return result[0] if single else result

    def assign_cluster(self, embedding: np.ndarray) -> dict:
        """
        Assign user to a cluster and return plan template.

        embedding: (16,) or (n, 16)
        Returns dict with cluster_id, plan_template, and confidence.
        """
        if not self._loaded:
            self.load()

        single = embedding.ndim == 1
        if single:
            embedding = embedding.reshape(1, -1)

        cluster_ids = self.cluster_model.predict(embedding)
        # Distance to assigned centroid as confidence proxy
        distances = self.cluster_model.kmeans.transform(embedding)

        results = []
        template_keys = list(CLUSTER_PLAN_TEMPLATES.keys())

        for i in range(len(cluster_ids)):
            cid = int(cluster_ids[i])
            dist = float(distances[i, cid])

            # Map cluster to nearest archetype template
            template_key = template_keys[cid % len(template_keys)]
            template = CLUSTER_PLAN_TEMPLATES[template_key]

            results.append({
                "cluster_id": cid,
                "archetype": template_key,
                "plan_template": template,
                "centroid_distance": round(dist, 4),
            })

        return results[0] if single else results

    def predict(self, user_features: np.ndarray) -> dict:
        """End-to-end: features → embedding → cluster → plan."""
        embedding = self.embed(user_features)
        cluster_info = self.assign_cluster(embedding)
        cluster_info["embedding"] = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
        return cluster_info


if __name__ == "__main__":
    predictor = UserEmbeddingPredictor()
    predictor.load()

    # Example with random user features
    dummy = np.random.randn(USER_FEATURE_DIM).astype(np.float32)
    result = predictor.predict(dummy)
    print(f"Cluster: {result['cluster_id']}, Archetype: {result['archetype']}")
    print(f"Plan: {result['plan_template']}")
