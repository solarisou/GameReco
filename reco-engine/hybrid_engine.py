import pandas as pd
from collaborative_filter import CollaborativeFilter
from content_filter import ContentFilter
from data_loader import load_ratings, load_items, load_history
from utils import logger, TOP_N, HYBRID_COLLAB_WEIGHT, HYBRID_CONTENT_WEIGHT


class HybridEngine:
    """
    Moteur hybride : combine le filtrage collaboratif (SVD)
    et le filtrage basé sur le contenu (TF-IDF).

    Score final = w_collab × score_collab + w_content × score_content
    + boost si l'item figure dans l'historique de consultation.
    """

    def __init__(self):
        logger.info("Chargement des données...")
        self.ratings_df = load_ratings()
        self.items_df   = load_items()

        self.collab  = CollaborativeFilter(self.ratings_df)
        self.content = ContentFilter(self.items_df)

        # Pré-entraînement
        self.collab.fit_svd()
        self.collab.fit_knn()
        self.content.fit()
        logger.info("Moteur hybride prêt")

    def recommend(self, user_id: str, item_type: str = None,
                  top_n: int = TOP_N) -> list:
        """
        Génère les recommandations hybrides pour un utilisateur.
        Gère le cold start : si l'utilisateur n'a pas de notes,
        retourne les items les mieux notés du catalogue.
        """
        # Items déjà notés par l'utilisateur
        user_ratings = self.ratings_df[
            self.ratings_df["user_id"] == user_id
        ]
        rated_ids = user_ratings["item_id"].tolist()

        # Cold start : aucune note
        if len(user_ratings) == 0:
            logger.info(f"Cold start pour {user_id} — top populaires")
            return self._popular_fallback(item_type, top_n)

        # Items bien notés (score >= 7) pour le content filter
        liked_ids = user_ratings[
            user_ratings["score"] >= 7
        ]["item_id"].tolist()

        # Historique de consultation (signal implicite)
        history_ids = set(load_history(user_id))

        # Scores collaboratifs (SVD)
        collab_results = self.collab.predict_svd(
            user_id, item_type, self.items_df
        )
        collab_map = {r["item_id"]: r["score"] for r in collab_results}

        # Scores contenu (TF-IDF)
        content_results = self.content.predict(
            liked_ids, item_type, exclude_ids=rated_ids
        )
        content_map = {r["item_id"]: r["score"] for r in content_results}

        # Union des items candidats
        all_items = set(collab_map.keys()) | set(content_map.keys())

        # Fusion pondérée
        fused = []
        for item_id in all_items:
            c_score = collab_map.get(item_id, 0.0)
            t_score = content_map.get(item_id, 0.0)
            score   = (HYBRID_COLLAB_WEIGHT  * c_score +
                       HYBRID_CONTENT_WEIGHT * t_score)

            # Boost historique (+10%)
            if item_id in history_ids and item_id not in rated_ids:
                score *= 1.1

            fused.append({
                "item_id": item_id,
                "score":   round(score, 4),
                "method":  "hybrid"
            })

        fused.sort(key=lambda x: x["score"], reverse=True)
        return fused[:top_n]

    def _popular_fallback(self, item_type: str = None,
                          top_n: int = TOP_N) -> list:
        """
        Fallback cold start : retourne les items les plus populaires
        (avg_rating × nombre de notes).
        """
        df = self.items_df.copy()
        if item_type:
            df = df[df["type"] == item_type]

        # Compte les notes par item
        counts = self.ratings_df.groupby("item_id").size().reset_index(
            name="count"
        )
        df = df.merge(counts, left_on="id", right_on="item_id", how="left")
        df["count"]      = df["count"].fillna(0)
        df["popularity"] = df["avg_rating"] * df["count"]

        top = df.nlargest(top_n, "popularity")
        return [
            {"item_id": row["id"], "score": round(row["avg_rating"], 4),
             "method": "popular"}
            for _, row in top.iterrows()
        ]
