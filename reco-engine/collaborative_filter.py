import numpy as np
from sklearn.neighbors import NearestNeighbors
from preprocessor import encode_users_items, normalize_scores
from utils import logger, TOP_N


class CollaborativeFilter:
    """
    Filtrage collaboratif avec deux approches :
    - SVD (décomposition en valeurs singulières) via numpy
    - KNN user-based via scikit-learn
    """

    def __init__(self, ratings_df, n_factors=50):
        self.n_factors = n_factors
        self.matrix, self.user2idx, self.item2idx, self.idx2item = \
            encode_users_items(ratings_df)
        self.U = None
        self.sigma = None
        self.Vt = None
        self.knn_model = None

    # ── SVD ──────────────────────────────────────────────────

    def fit_svd(self):
        """
        Décompose la matrice user-item : M = U × Σ × Vt
        Réduit aux n_factors composantes principales.
        """
        U, sigma, Vt = np.linalg.svd(self.matrix, full_matrices=False)
        # Tronquer aux k facteurs latents
        k = min(self.n_factors, len(sigma))
        self.U     = U[:, :k]
        self.sigma = sigma[:k]
        self.Vt    = Vt[:k, :]
        logger.info(f"SVD entraîné — {k} facteurs latents")

    def predict_svd(self, user_id: str, item_type: str = None,
                    items_df=None) -> list:
        """
        Retourne les TOP_N recommandations pour un utilisateur via SVD.
        """
        if self.U is None:
            self.fit_svd()

        user_idx = self.user2idx.get(user_id)
        if user_idx is None:
            logger.warning(f"Utilisateur inconnu pour SVD : {user_id}")
            return []

        # Reconstruit le vecteur de scores prédit pour cet utilisateur
        user_vec  = self.U[user_idx] * self.sigma
        scores    = user_vec @ self.Vt            # shape: (n_items,)
        scores_norm = normalize_scores(scores)

        # Exclut les items déjà notés
        rated_mask = self.matrix[user_idx] > 0
        scores_norm[rated_mask] = -1

        # Filtre par type si demandé
        if item_type and items_df is not None:
            type_items = set(
                items_df[items_df["type"] == item_type]["id"].tolist()
            )
            for idx, item_id in self.idx2item.items():
                if item_id not in type_items:
                    scores_norm[idx] = -1

        top_indices = np.argsort(scores_norm)[::-1][:TOP_N]
        results = [
            {"item_id": self.idx2item[i], "score": float(scores_norm[i])}
            for i in top_indices if scores_norm[i] >= 0
        ]
        return results

    # ── KNN user-based ───────────────────────────────────────

    def fit_knn(self, n_neighbors=10):
        n_users = self.matrix.shape[0]
        if n_users == 0:
            logger.warning("Pas d'utilisateurs — KNN ignoré")
            return
        self.knn_model = NearestNeighbors(
            n_neighbors=min(n_neighbors, n_users),
            metric="cosine",
            algorithm="brute"
        )
        self.knn_model.fit(self.matrix)
        logger.info("KNN user-based entraîné")

    def predict_knn(self, user_id: str) -> list:
        """
        Retourne les TOP_N recommandations basées sur les utilisateurs similaires.
        """
        if self.knn_model is None:
            self.fit_knn()

        user_idx = self.user2idx.get(user_id)
        if user_idx is None:
            logger.warning(f"Utilisateur inconnu pour KNN : {user_id}")
            return []

        user_vec = self.matrix[user_idx].reshape(1, -1)
        distances, neighbor_indices = self.knn_model.kneighbors(user_vec)

        # Agrège les notes des voisins
        neighbor_matrix = self.matrix[neighbor_indices[0]]
        weights = 1 - distances[0]                # similarité cosinus
        weighted_scores = weights @ neighbor_matrix

        # Exclut les items déjà notés
        rated_mask = self.matrix[user_idx] > 0
        weighted_scores[rated_mask] = -1

        scores_norm = normalize_scores(weighted_scores)
        top_indices = np.argsort(scores_norm)[::-1][:TOP_N]

        results = [
            {"item_id": self.idx2item[i], "score": float(scores_norm[i])}
            for i in top_indices if scores_norm[i] >= 0
        ]
        return results