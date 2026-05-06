import pandas as pd
import numpy as np
from utils import logger


def encode_users_items(ratings_df: pd.DataFrame):
    """
    Encode user_id et item_id en indices entiers.
    Retourne la matrice user-item, les mappings id→index et index→id.
    """
    users = ratings_df["user_id"].unique()
    items = ratings_df["item_id"].unique()

    user2idx = {u: i for i, u in enumerate(users)}
    item2idx = {it: i for i, it in enumerate(items)}
    idx2item = {i: it for it, i in item2idx.items()}

    n_users = len(users)
    n_items = len(items)

    # Matrice user-item (sparse via numpy, 0 = non noté)
    matrix = np.zeros((n_users, n_items), dtype=np.float32)
    for _, row in ratings_df.iterrows():
        u = user2idx.get(row["user_id"])
        it = item2idx.get(row["item_id"])
        if u is not None and it is not None:
            matrix[u, it] = row["score"]

    logger.info(f"Matrice user-item : {n_users} users × {n_items} items")
    return matrix, user2idx, item2idx, idx2item


def normalize_scores(scores: np.ndarray) -> np.ndarray:
    """
    Normalise un vecteur de scores entre 0 et 1.
    """
    min_s = scores.min()
    max_s = scores.max()
    if max_s - min_s == 0:
        return np.zeros_like(scores)
    return (scores - min_s) / (max_s - min_s)


def clean_text(text: str) -> str:
    """
    Nettoyage basique du texte pour TF-IDF.
    """
    if not isinstance(text, str):
        return ""
    return text.lower().strip()
