import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import numpy as np
import tensorflow as tf
import tensorflow_recommenders as tfrs
from utils import logger

# ── 1. GÉNÉRATION DES DONNÉES SYNTHÉTIQUES ───────────────────

NUM_USERS  = 200
NUM_ITEMS  = 500
NUM_RATINGS = 5000

logger.info(f"Génération de {NUM_RATINGS} interactions synthétiques...")

np.random.seed(42)

user_ids  = [f"user_{i}"  for i in range(NUM_USERS)]
item_ids  = [f"item_{i}"  for i in range(NUM_ITEMS)]

# Simulation d'interactions : chaque user note entre 10 et 40 items
interactions = []
for user in user_ids:
    n = np.random.randint(10, 40)
    items_rated = np.random.choice(item_ids, size=n, replace=False)
    for item in items_rated:
        interactions.append({"user_id": user, "item_id": item})

logger.info(f"{len(interactions)} interactions générées")

# Conversion en tf.data.Dataset
ratings_ds = tf.data.Dataset.from_tensor_slices({
    "user_id": [r["user_id"] for r in interactions],
    "item_id": [r["item_id"] for r in interactions],
}).shuffle(len(interactions), seed=42)

# Dataset des items (pour la tâche de retrieval)
items_ds = tf.data.Dataset.from_tensor_slices(item_ids)

# Split train / test (80/20)
n_train = int(len(interactions) * 0.8)
train_ds = ratings_ds.take(n_train)
test_ds  = ratings_ds.skip(n_train)

logger.info(f"Train : {n_train} | Test : {len(interactions) - n_train}")

# ── 2. TOURS (TOWERS) ────────────────────────────────────────

class UserTower(tf.keras.Model):
    def __init__(self, user_ids, embedding_dim=32):
        super().__init__()
        self.embedding = tf.keras.Sequential([
            tf.keras.layers.StringLookup(vocabulary=user_ids, mask_token=None),
            tf.keras.layers.Embedding(len(user_ids) + 1, embedding_dim)
        ])

    def call(self, user_id):
        return self.embedding(user_id)


class ItemTower(tf.keras.Model):
    def __init__(self, item_ids, embedding_dim=32):
        super().__init__()
        self.embedding = tf.keras.Sequential([
            tf.keras.layers.StringLookup(vocabulary=item_ids, mask_token=None),
            tf.keras.layers.Embedding(len(item_ids) + 1, embedding_dim)
        ])

    def call(self, item_id):
        return self.embedding(item_id)


# ── 3. MODÈLE TWO-TOWER ──────────────────────────────────────

class TwoTowerModel(tfrs.Model):
    def __init__(self, user_ids, item_ids, items_ds, embedding_dim=32):
        super().__init__()
        self.user_tower = UserTower(user_ids, embedding_dim)
        self.item_tower = ItemTower(item_ids, embedding_dim)

        self.task = tfrs.tasks.Retrieval(
            metrics=tfrs.metrics.FactorizedTopK(
                candidates=items_ds.batch(64).map(self.item_tower)
            )
        )

    def compute_loss(self, features, training=False):
        user_emb = self.user_tower(features["user_id"])
        item_emb = self.item_tower(features["item_id"])
        return self.task(user_emb, item_emb)


# ── 4. ENTRAÎNEMENT ──────────────────────────────────────────

logger.info("Construction du modèle Two-Tower...")

model = TwoTowerModel(user_ids, item_ids, items_ds, embedding_dim=32)
model.compile(optimizer=tf.keras.optimizers.Adagrad(learning_rate=0.1))

logger.info("Entraînement sur 5 époques...")
history = model.fit(
    train_ds.batch(64),
    epochs=5,
    verbose=1
)

# ── 5. ÉVALUATION ────────────────────────────────────────────

logger.info("Évaluation sur le jeu de test...")
results = model.evaluate(test_ds.batch(64), return_dict=True, verbose=1)

logger.info("=== Résultats ===")
for k, v in results.items():
    logger.info(f"  {k} : {v:.4f}")

# ── 6. TEST DE PRÉDICTION ────────────────────────────────────

logger.info("Test de prédiction pour user_0...")

index = tfrs.layers.factorized_top_k.BruteForce(model.user_tower)
index.index_from_dataset(
    items_ds.batch(64).map(lambda x: (x, model.item_tower(x)))
)

_, top_items = index(tf.constant(["user_0"]))
logger.info("Top 5 recommandations pour user_0 :")
for item in top_items[0][:5].numpy():
    logger.info(f"  → {item.decode('utf-8')}")

logger.info("TFRS validé — pipeline opérationnel")