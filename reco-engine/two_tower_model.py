import os
os.environ["TF_USE_LEGACY_KERAS"]    = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"]  = "0"

import numpy as np
import pandas as pd
import tensorflow as tf
import tensorflow_recommenders as tfrs
from data_loader import load_ratings, load_items
from utils import logger, TOP_N


# ─────────────────────────────────────────────────────────
# 1. TOURS
# ─────────────────────────────────────────────────────────

class UserTower(tf.keras.Model):
    def __init__(self, user_ids: list, embedding_dim: int = 32):
        super().__init__()
        self.embedding = tf.keras.Sequential([
            tf.keras.layers.StringLookup(vocabulary=user_ids, mask_token=None),
            tf.keras.layers.Embedding(len(user_ids) + 1, embedding_dim)
        ])

    def call(self, user_id):
        return self.embedding(user_id)


class ItemTower(tf.keras.Model):
    def __init__(self, item_ids: list, embedding_dim: int = 32):
        super().__init__()
        self.embedding = tf.keras.Sequential([
            tf.keras.layers.StringLookup(vocabulary=item_ids, mask_token=None),
            tf.keras.layers.Embedding(len(item_ids) + 1, embedding_dim)
        ])

    def call(self, item_id):
        return self.embedding(item_id)


# ─────────────────────────────────────────────────────────
# 2. MODELE COMPLET
# ─────────────────────────────────────────────────────────

class TwoTowerModel(tfrs.Model):
    def __init__(self, user_ids, item_ids, items_dataset, embedding_dim=32):
        super().__init__()
        self.user_tower = UserTower(user_ids, embedding_dim)
        self.item_tower = ItemTower(item_ids, embedding_dim)
        self.task = tfrs.tasks.Retrieval(
            metrics=tfrs.metrics.FactorizedTopK(
                candidates=items_dataset.batch(128).map(self.item_tower)
            )
        )

    def compute_loss(self, features, training=False):
        user_emb = self.user_tower(features["user_id"])
        item_emb = self.item_tower(features["item_id"])
        return self.task(user_emb, item_emb)


# ─────────────────────────────────────────────────────────
# 3. ENTRAÎNEMENT
# ─────────────────────────────────────────────────────────

def train_two_tower(epochs: int = 5, embedding_dim: int = 32, batch_size: int = 64):
    logger.info("Two-Tower : chargement des données...")
    ratings_df = load_ratings()
    items_df   = load_items()

    if len(ratings_df) < 10:
        logger.warning("Pas assez de ratings pour entraîner Two-Tower (minimum 10)")
        return None, None, None

    ratings_df["user_id"] = ratings_df["user_id"].astype(str)
    ratings_df["item_id"] = ratings_df["item_id"].astype(str)
    items_df["id"]        = items_df["id"].astype(str)

    user_ids = ratings_df["user_id"].unique().tolist()
    item_ids = items_df["id"].unique().tolist()

    ratings_ds = tf.data.Dataset.from_tensor_slices({
        "user_id": ratings_df["user_id"].values,
        "item_id": ratings_df["item_id"].values,
    }).shuffle(len(ratings_df))

    items_ds = tf.data.Dataset.from_tensor_slices(items_df["id"].values)

    model = TwoTowerModel(user_ids, item_ids, items_ds, embedding_dim)
    model.compile(optimizer=tf.keras.optimizers.Adagrad(learning_rate=0.1))

    logger.info(f"Two-Tower : entraînement ({epochs} époques, {len(ratings_df)} ratings)...")
    model.fit(ratings_ds.batch(batch_size), epochs=epochs, verbose=0)
    logger.info("Two-Tower : entraînement terminé !")

    # Index de recherche rapide
    index = tfrs.layers.factorized_top_k.BruteForce(model.user_tower)
    index.index_from_dataset(
        items_ds.batch(128).map(lambda x: (x, model.item_tower(x)))
    )

    return model, index, item_ids


# ─────────────────────────────────────────────────────────
# 4. PRÉDICTION
# ─────────────────────────────────────────────────────────

def predict_two_tower(index, user_id: str, top_n: int = TOP_N,
                      exclude_ids: list = None) -> list:
    if index is None:
        return []

    exclude_ids = set(exclude_ids or [])

    try:
        _, item_ids = index(tf.constant([str(user_id)]))
        results = []
        for item_id in item_ids[0].numpy():
            iid = item_id.decode("utf-8")
            if iid in exclude_ids:
                continue
            results.append({
                "item_id": iid,
                "score":   1.0,
                "method":  "two_tower"
            })
            if len(results) >= top_n:
                break
        return results
    except Exception as e:
        logger.error(f"Two-Tower predict error: {e}")
        return []