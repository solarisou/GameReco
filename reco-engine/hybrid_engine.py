import threading
import time
from collaborative_filter import CollaborativeFilter
from content_filter import ContentFilter
from data_loader import load_ratings, load_items, load_history
from two_tower_model import train_two_tower, predict_two_tower
from utils import (logger, TOP_N,
                   HYBRID_COLLAB_WEIGHT, HYBRID_CONTENT_WEIGHT, HYBRID_TWOTOWER_WEIGHT,
                   TWOTOWER_EPOCHS, TWOTOWER_BATCH_SIZE, TWOTOWER_EMB_DIM)


class HybridEngine:
    """
    Moteur hybride combinant trois approches :
      - Filtrage collaboratif  (SVD via numpy)         — poids configurable
      - Filtrage contenu       (TF-IDF + cosinus)      — poids configurable
      - Two-Tower              (TensorFlow/Keras)       — poids configurable

    Score final = w_collab * s_collab
                + w_content * s_content
                + w_twotower * s_twotower   (0 si Two-Tower non disponible)

    Réentraînement thread-safe : swap atomique sous verrou.
    Pendant l'entraînement, l'ancien moteur continue de servir les requêtes.
    """

    def __init__(self):
        self._lock = threading.Lock()

        self._retrain_status = {
            "is_training":  False,
            "last_trained": None,
            "trained_on":   {"ratings": 0, "items": 0},
            "two_tower":    "disabled"   # "disabled" | "training" | "ready"
        }

        logger.info("Chargement initial du moteur hybride...")
        self._do_load()
        logger.info("Moteur hybride prêt")

    # ── Chargement / entraînement ─────────────────────────────

    def _do_load(self):
        """
        Entraîne les trois modèles et stocke les résultats sur self.
        Appelé au démarrage et depuis le thread de réentraînement.
        """
        ratings_df = load_ratings()
        items_df   = load_items()

        # ── SVD + KNN ─────────────────────────────────────────
        collab = CollaborativeFilter(ratings_df)
        collab.fit_svd()
        collab.fit_knn()

        # ── TF-IDF ────────────────────────────────────────────
        content = ContentFilter(items_df)
        content.fit()

        # ── Two-Tower ─────────────────────────────────────────
        tt_model = None
        tt_index = None

        if len(ratings_df) >= 10:   # pas la peine d'entraîner sur trop peu de données
            logger.info("Entraînement Two-Tower...")
            try:
                tt_model, tt_index, _ = train_two_tower(
                    epochs     = TWOTOWER_EPOCHS,
                    embedding_dim = TWOTOWER_EMB_DIM,
                    batch_size = TWOTOWER_BATCH_SIZE
                )
                self._retrain_status["two_tower"] = "ready"
                logger.info("Two-Tower entraîné")
            except Exception as e:
                logger.error(f"Two-Tower échoué (SVD+Content seuls actifs) : {e}")
                self._retrain_status["two_tower"] = "disabled"
        else:
            logger.info(f"Pas assez de ratings ({len(ratings_df)}) — Two-Tower ignoré")
            self._retrain_status["two_tower"] = "disabled"

        # ── Swap atomique ─────────────────────────────────────
        with self._lock:
            self._collab      = collab
            self._content     = content
            self._tt_index    = tt_index
            self._ratings_df  = ratings_df
            self._items_df    = items_df

        self._retrain_status["last_trained"]          = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._retrain_status["trained_on"]["ratings"] = len(ratings_df)
        self._retrain_status["trained_on"]["items"]   = len(items_df)

    # ── Réentraînement en arrière-plan ────────────────────────

    def retrain(self) -> bool:
        """
        Lance un réentraînement complet dans un thread daemon.
        Retourne False si un entraînement est déjà en cours.
        """
        if self._retrain_status["is_training"]:
            logger.warning("Réentraînement déjà en cours — ignoré")
            return False

        def _worker():
            self._retrain_status["is_training"] = True
            self._retrain_status["two_tower"]   = "training"
            start = time.time()
            try:
                self._do_load()
                elapsed = round(time.time() - start, 1)
                logger.info(f"Réentraînement terminé en {elapsed}s")
            except Exception as e:
                logger.error(f"Erreur réentraînement : {e}")
            finally:
                self._retrain_status["is_training"] = False

        threading.Thread(target=_worker, daemon=True).start()
        return True

    def get_status(self) -> dict:
        return dict(self._retrain_status)

    # ── Recommandations ───────────────────────────────────────

    def recommend(self, user_id: str, item_type: str = None,
                  top_n: int = TOP_N) -> list:
        """
        Génère les recommandations hybrides pour un utilisateur.
        """
        # Lecture thread-safe de l'engine courant
        with self._lock:
            collab     = self._collab
            content    = self._content
            tt_index   = self._tt_index
            ratings_df = self._ratings_df
            items_df   = self._items_df

        user_ratings = ratings_df[ratings_df["user_id"] == user_id]
        rated_ids    = user_ratings["item_id"].tolist()

        # Cold start
        if len(user_ratings) == 0:
            logger.info(f"Cold start pour {user_id} — top populaires")
            return self._popular_fallback(ratings_df, items_df, item_type, top_n)

        liked_ids   = user_ratings[user_ratings["score"] >= 7]["item_id"].tolist()
        history_ids = set(load_history(user_id))

        # ── Scores collaboratifs (SVD) ────────────────────────
        collab_results = collab.predict_svd(user_id, item_type, items_df)
        collab_map     = {r["item_id"]: r["score"] for r in collab_results}

        # ── Scores contenu (TF-IDF) ───────────────────────────
        content_results = content.predict(liked_ids, item_type, exclude_ids=rated_ids)
        content_map     = {r["item_id"]: r["score"] for r in content_results}

        # ── Scores Two-Tower ──────────────────────────────────
        tt_map = {}
        if tt_index is not None:
            try:
                tt_results = predict_two_tower(tt_index, user_id, top_n=top_n * 2)
                tt_map = {r["item_id"]: r["score"] for r in tt_results}
            except Exception as e:
                logger.warning(f"Two-Tower predict échoué : {e}")

        # ── Fusion pondérée ───────────────────────────────────
        all_items = set(collab_map.keys()) | set(content_map.keys()) | set(tt_map.keys())

        # Si Two-Tower non disponible, redistribuer son poids
        if tt_map:
            w_collab  = HYBRID_COLLAB_WEIGHT
            w_content = HYBRID_CONTENT_WEIGHT
            w_tt      = HYBRID_TWOTOWER_WEIGHT
        else:
            total = HYBRID_COLLAB_WEIGHT + HYBRID_CONTENT_WEIGHT
            w_collab  = HYBRID_COLLAB_WEIGHT  / total
            w_content = HYBRID_CONTENT_WEIGHT / total
            w_tt      = 0.0

        fused = []
        for item_id in all_items:
            score = (w_collab  * collab_map.get(item_id, 0.0) +
                     w_content * content_map.get(item_id, 0.0) +
                     w_tt      * tt_map.get(item_id, 0.0))

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

    # ── Cold start fallback ───────────────────────────────────

    def _popular_fallback(self, ratings_df, items_df,
                          item_type=None, top_n=TOP_N) -> list:
        import pandas as pd
        df = items_df.copy()
        if item_type:
            df = df[df["type"] == item_type]

        counts = ratings_df.groupby("item_id").size().reset_index(name="count")
        df = df.merge(counts, left_on="id", right_on="item_id", how="left")
        df["count"]      = df["count"].fillna(0)
        df["popularity"] = df["avg_rating"] * df["count"]

        top = df.nlargest(top_n, "popularity")
        return [
            {"item_id": row["id"], "score": round(row["avg_rating"], 4),
             "method": "popular"}
            for _, row in top.iterrows()
        ]