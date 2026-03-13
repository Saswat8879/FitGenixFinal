"""
FitGenix ML — Train User Embedding & Clustering
Autoencoder + KMeans on synthetic user profiles.
Run: python -m ml.training.train_user_embedding
"""
import sys, os
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler
import joblib
from tqdm import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    AUTOENCODER_PARAMS, CLUSTER_K_RANGE, CLUSTER_DEFAULT_K,
    USER_FEATURE_DIM, EMBEDDING_DIM, SAVED_MODELS_DIR, PROCESSED_DIR,
    SYNTHETIC_DIR, RANDOM_SEED,
)
from utils import save_torch_model, save_sklearn_model, get_device, set_seed, logger
from models.user_embedding import UserAutoencoder, UserClusterModel, CLUSTER_PLAN_TEMPLATES


def train_autoencoder(X: np.ndarray, device: torch.device) -> tuple[UserAutoencoder, np.ndarray]:
    """Train the user autoencoder and return model + embeddings."""
    p = AUTOENCODER_PARAMS

    # Scale to [0, 1] for sigmoid output
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X).astype(np.float32)
    joblib.dump(scaler, PROCESSED_DIR / "user_feature_scaler.joblib")

    dataset = TensorDataset(torch.from_numpy(X_scaled))
    loader = DataLoader(dataset, batch_size=p["batch_size"], shuffle=True, drop_last=False)

    model = UserAutoencoder(
        input_dim=X_scaled.shape[1],
        hidden_dim=p["hidden_dim"],
        embedding_dim=p["embedding_dim"],
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=p["lr"], weight_decay=p["weight_decay"])
    criterion = nn.MSELoss()

    logger.info(f"Training autoencoder: {X_scaled.shape[1]}-dim → {p['embedding_dim']}-dim")
    logger.info(f"  Device: {device}, Epochs: {p['epochs']}, Batch: {p['batch_size']}")

    best_loss = float("inf")
    patience, patience_counter = 15, 0

    for epoch in tqdm(range(p["epochs"]), desc="Autoencoder training", unit="epoch"):
        model.train()
        epoch_loss = 0.0
        for (batch_x,) in loader:
            batch_x = batch_x.to(device)
            recon, _ = model(batch_x)
            loss = criterion(recon, batch_x)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * batch_x.size(0)

        epoch_loss /= len(X_scaled)
        if (epoch + 1) % 10 == 0:
            logger.info(f"  Epoch {epoch+1}/{p['epochs']} — Loss: {epoch_loss:.6f}")

        if epoch_loss < best_loss - 1e-6:
            best_loss = epoch_loss
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"  Early stopping at epoch {epoch+1}")
                break

    # Extract embeddings
    model.eval()
    X_tensor = torch.from_numpy(X_scaled).to(device)
    with torch.no_grad():
        embeddings = model.encode(X_tensor).cpu().numpy()

    logger.info(f"  Final reconstruction loss: {best_loss:.6f}")
    logger.info(f"  Embedding shape: {embeddings.shape}")

    return model, embeddings


def find_best_k(embeddings: np.ndarray) -> int:
    """Find optimal k using silhouette score."""
    best_k, best_score = CLUSTER_DEFAULT_K, -1

    logger.info("Searching for optimal k...")
    for k in tqdm(list(CLUSTER_K_RANGE), desc="Cluster search", unit="k"):
        cm = UserClusterModel(n_clusters=k, random_state=RANDOM_SEED)
        cm.fit(embeddings)
        score = cm.score(embeddings)
        logger.info(f"  k={k}: silhouette={score:.4f}")
        if score > best_score:
            best_score = score
            best_k = k

    logger.info(f"  Best k={best_k} (silhouette={best_score:.4f})")
    return best_k


def train_user_embedding():
    set_seed(RANDOM_SEED)
    device = get_device()

    # Load synthetic user profiles
    synth_path = SYNTHETIC_DIR / "user_profiles.npy"
    if not synth_path.exists():
        logger.error(f"Synthetic data not found at {synth_path}")
        logger.error("Run `python -m ml.data.synthetic_generator` first!")
        return

    X_users = np.load(synth_path)
    logger.info(f"Loaded {X_users.shape[0]} user profiles ({X_users.shape[1]} dims)")

    # 1. Train autoencoder
    ae_model, embeddings = train_autoencoder(X_users, device)
    save_torch_model(ae_model, "user_autoencoder", SAVED_MODELS_DIR,
                     metadata={"input_dim": X_users.shape[1], "embedding_dim": EMBEDDING_DIM})

    # Save embeddings for downstream use
    np.save(PROCESSED_DIR / "user_embeddings.npy", embeddings)

    # 2. Find best k and train clustering
    best_k = find_best_k(embeddings)
    cluster_model = UserClusterModel(n_clusters=best_k, random_state=RANDOM_SEED)
    cluster_model.fit(embeddings)

    labels = cluster_model.predict(embeddings)
    sil_score = cluster_model.score(embeddings)

    logger.info(f"Final clustering: k={best_k}, silhouette={sil_score:.4f}")
    unique, counts = np.unique(labels, return_counts=True)
    for c, n in zip(unique, counts):
        logger.info(f"  Cluster {c}: {n} users ({n/len(labels)*100:.1f}%)")

    # 3. Map clusters to plan templates (heuristic: by centroid similarity)
    template_names = list(CLUSTER_PLAN_TEMPLATES.keys())
    for i in range(min(best_k, len(template_names))):
        cluster_model.set_cluster_profile(i, CLUSTER_PLAN_TEMPLATES[template_names[i]])

    save_sklearn_model(cluster_model, "user_cluster_model", SAVED_MODELS_DIR,
                       metadata={"k": best_k, "silhouette": sil_score})

    logger.info("User embedding & clustering training complete!")
    return {"silhouette": sil_score, "k": best_k}


if __name__ == "__main__":
    train_user_embedding()
