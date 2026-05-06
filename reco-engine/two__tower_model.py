import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import numpy as np
import pandas as pd
import tensorflow as tf
import tensorflow_recommenders as tfrs
from data_loader import load_ratings, load_items
from utils import logger

# ──────────────────────────────────────────────
# 1. TOURS (Towers)
# ──────────────────────────────────────────────

class UserTower(tf.keras.Model):
    """
    Transforme un user_id (string) en vecteur de dimension embedding_dim.
    """
    def __init__(self, user_ids: list, embedding_dim: int = 32):
        super().__init__()
        self.embedding = tf.keras.Sequential([
            tf.keras.layers.StringLookup(
                vocabulary=user_ids, mask_token=None
            ),
            tf.keras.layers.Embedding(
                input_dim=len(user_ids) + 1,
                output_dim=embedding_dim
            )
        ])

    def call(self, user_id):
        return self.embedding(user_id)


class ItemTower(tf.keras.Model):
    """
    Transforme un item_id (string) en vecteur de dimension embedding_dim.
    """
    def __init__(self, item_ids: list, embedding_dim: int = 32):
        super().__init__()
        self.embedding = tf.keras.Sequential([
            tf.keras.layers.StringLookup(
                vocabulary=item_ids, mask_token=None
            ),
            tf.keras.layers.Embedding(
                input_dim=len(item_ids) + 1,
                output_dim=embedding_dim
            )
        ])

    def call(self, item_id):
        return self.embedding(item_id)


# ──────────────────────────────────────────────
# 2. MODÈLE COMPLET
# ──────────────────────────────────────────────

class TwoTowerModel(tfrs.Model):
    """
    Modèle two-tower complet :
    - user_tower  : encode l'utilisateur
    - item_tower  : encode l'item
    - task        : retrieval (trouve les items les plus proches)
    """
    def __init__(self, user_ids: list, item_ids: list,
                 items_dataset: tf.data.Dataset, embedding_dim: int = 32):
        super().__init__()

        self.user_tower = UserTower(user_ids, embedding_dim)
        self.item_tower = ItemTower(item_ids, embedding_dim)

        # Task : retrieval — optimise le produit scalaire user/item
        self.task = tfrs.tasks.Retrieval(
            metrics=tfrs.metrics.FactorizedTopK(
                candidates=items_dataset.batch(128).map(self.item_tower)
            )
        )

    def compute_loss(self, features, training=False):
        user_emb = self.user_tower(features["user_id"])
        item_emb = self.item_tower(features["item_id"])
        return self.task(user_emb, item_emb)


# ──────────────────────────────────────────────
# 3. ENTRAÎNEMENT
# ──────────────────────────────────────────────

def train_two_tower(epochs: int = 5, embedding_dim: int = 32,
                    batch_size: int = 64):
    logger.info("Chargement des données pour Two-Tower...")
    ratings_df = load_ratings()
    items_df   = load_items()

    if len(ratings_df) == 0:
        logger.warning("Aucun rating en base — Two-Tower ignoré")
        return None, None

    # Conversion en strings (requis par StringLookup)
    ratings_df["user_id"] = ratings_df["user_id"].astype(str)
    ratings_df["item_id"] = ratings_df["item_id"].astype(str)
    items_df["id"]        = items_df["id"].astype(str)

    user_ids = ratings_df["user_id"].unique().tolist()
    item_ids = items_df["id"].unique().tolist()

    # Dataset TensorFlow
    ratings_ds = tf.data.Dataset.from_tensor_slices({
        "user_id": ratings_df["user_id"].values,
        "item_id": ratings_df["item_id"].values,
    }).shuffle(len(ratings_df))

    items_ds = tf.data.Dataset.from_tensor_slices(
        items_df["id"].values
    )

    # Modèle
    model = TwoTowerModel(user_ids, item_ids, items_ds, embedding_dim)
    model.compile(optimizer=tf.keras.optimizers.Adagrad(learning_rate=0.1))

    # Entraînement
    logger.info(f"Entraînement Two-Tower — {epochs} époques...")
    model.fit(ratings_ds.batch(batch_size), epochs=epochs, verbose=1)
    logger.info("Two-Tower entraîné !")

    # Index de recherche rapide
    index = tfrs.layers.factorized_top_k.BruteForce(model.user_tower)
    index.index_from_dataset(
        items_ds.batch(128).map(
            lambda x: (x, model.item_tower(x))
        )
    )

    return model, index


# ──────────────────────────────────────────────
# 4. PRÉDICTION
# ──────────────────────────────────────────────

def predict_two_tower(index, user_id: str, top_n: int = 10) -> list:
    """
    Retourne les top_n items recommandés pour un utilisateur.
    """
    if index is None:
        return []

    _, item_ids = index(tf.constant([user_id]))
    results = []
    for item_id in item_ids[0][:top_n].numpy():
        results.append({
            "item_id": item_id.decode("utf-8"),
            "score":   1.0,
            "method":  "two_tower"
        })
    return results


# ──────────────────────────────────────────────
# 5. TEST RAPIDE
# ──────────────────────────────────────────────

if __name__ == "__main__":
    model, index = train_two_tower(epochs=3)
    if index:
        results = predict_two_tower(index, "test-user", top_n=5)
        print("Recommandations :", results)