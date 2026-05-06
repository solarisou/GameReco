import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from preprocessor import clean_text, normalize_scores
from utils import logger, TOP_N


class ContentFilter:
    """
    Filtrage basé sur le contenu via TF-IDF + similarité cosinus.
    Exploite les métadonnées : titre, type, genres, synopsis.
    """

    def __init__(self, items_df: pd.DataFrame):
        self.items_df = items_df.copy()
        self.items_df["content"] = self.items_df["content"].apply(clean_text)
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words="english"
        )
        self.tfidf_matrix = None
        self.item_index = {
            row["id"]: idx
            for idx, row in self.items_df.iterrows()
        }

    def fit(self):
        if self.items_df.empty:
            logger.warning("Aucun item en BDD — TF-IDF ignoré")
            return
        self.tfidf_matrix = self.vectorizer.fit_transform(
            self.items_df["content"]
        )
        logger.info(f"TF-IDF entraîné — matrice : {self.tfidf_matrix.shape}")

    def predict(self, liked_item_ids: list, item_type: str = None,
                exclude_ids: list = None) -> list:
        """
        Retourne les TOP_N items les plus similaires aux items aimés.

        liked_item_ids : items que l'utilisateur a bien notés (score >= 7)
        item_type      : filtre optionnel 'manga' ou 'game'
        exclude_ids    : items déjà vus / notés à exclure
        """
        if self.tfidf_matrix is None:
            self.fit()

        if not liked_item_ids:
            return []

        exclude_ids = set(exclude_ids or [])

        # Profil utilisateur = moyenne des vecteurs TF-IDF des items aimés
        liked_indices = [
            self.item_index[iid]
            for iid in liked_item_ids
            if iid in self.item_index
        ]
        if not liked_indices:
            return []

        user_profile = np.asarray(
            self.tfidf_matrix[liked_indices].mean(axis=0)
        )
        sim_scores = cosine_similarity(
            user_profile, self.tfidf_matrix
        ).flatten()
        sim_scores = normalize_scores(sim_scores)

        # Filtre type et exclusions
        results = []
        for idx, score in enumerate(sim_scores):
            item = self.items_df.iloc[idx]
            if item["id"] in exclude_ids:
                continue
            if item["id"] in liked_item_ids:
                continue
            if item_type and item["type"] != item_type:
                continue
            results.append({
                "item_id": item["id"],
                "score": float(score)
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:TOP_N]