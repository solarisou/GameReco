import os
os.environ["TF_USE_LEGACY_KERAS"]   = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from flask import Flask, request, jsonify
from hybrid_engine import HybridEngine
from two_tower_model import train_two_tower, predict_two_tower
from data_loader import load_ratings
from utils import logger, FLASK_PORT, TOP_N

app = Flask(__name__)

# ── Moteur hybride (SVD + TF-IDF) ────────────────────────
logger.info("Initialisation du moteur hybride...")
engine = HybridEngine()

# ── Moteur Two-Tower (TFRS) ───────────────────────────────
# Entraîné au démarrage — retombe sur hybride si pas assez de données
logger.info("Initialisation du modèle Two-Tower...")
_tt_model, _tt_index, _tt_item_ids = train_two_tower(epochs=5)

if _tt_index is not None:
    logger.info("Two-Tower prêt et actif")
else:
    logger.warning("Two-Tower non disponible — moteur hybride utilisé par défaut")


def _has_enough_ratings(user_id: str, min_ratings: int = 5) -> bool:
    """Vérifie si l'utilisateur a assez de notes pour Two-Tower."""
    try:
        ratings_df = load_ratings()
        user_ratings = ratings_df[ratings_df["user_id"] == user_id]
        return len(user_ratings) >= min_ratings
    except Exception:
        return False


# ─────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":      "ok",
        "service":     "reco-engine",
        "two_tower":   "active" if _tt_index is not None else "inactive",
        "hybrid":      "active"
    })


@app.route("/recommend", methods=["POST"])
def recommend():
    """
    Body JSON :
    {
        "user_id": "uuid",
        "type":    "manga" | "game" | null,
        "top_n":   10,
        "engine":  "auto" | "hybrid" | "two_tower"   (optionnel, défaut: auto)
    }

    Logique "auto" :
      - Two-Tower si le modèle est prêt ET l'utilisateur a >= 5 notes
      - Hybride sinon
    """
    data      = request.get_json()
    user_id   = data.get("user_id")
    item_type = data.get("type")
    top_n     = int(data.get("top_n", TOP_N))
    engine_choice = data.get("engine", "auto")

    if not user_id:
        return jsonify({"error": "user_id requis"}), 400

    try:
        use_two_tower = (
            engine_choice == "two_tower"
            or (
                engine_choice == "auto"
                and _tt_index is not None
                and _has_enough_ratings(user_id)
            )
        )

        if use_two_tower:
            logger.info(f"Two-Tower utilisé pour {user_id}")
            # Items déjà notés à exclure
            ratings_df   = load_ratings()
            rated_ids    = ratings_df[ratings_df["user_id"] == user_id]["item_id"].tolist()
            results      = predict_two_tower(_tt_index, user_id, top_n, exclude_ids=rated_ids)

            # Si Two-Tower ne retourne rien (utilisateur inconnu du modèle)
            # on retombe sur le hybride
            if not results:
                logger.warning(f"Two-Tower vide pour {user_id} — fallback hybride")
                results = engine.recommend(user_id, item_type, top_n)
                method  = "hybrid_fallback"
            else:
                method = "two_tower"
        else:
            logger.info(f"Moteur hybride utilisé pour {user_id}")
            results = engine.recommend(user_id, item_type, top_n)
            method  = "hybrid"

        return jsonify({
            "user_id":         user_id,
            "engine_used":     method,
            "recommendations": results
        })

    except Exception as e:
        logger.error(f"Erreur recommend : {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/recommend/retrain", methods=["POST"])
def retrain():
    """
    Réentraîne le modèle Two-Tower avec les données actuelles.
    À appeler après un ajout massif de notes.
    """
    global _tt_model, _tt_index, _tt_item_ids
    try:
        logger.info("Réentraînement Two-Tower demandé...")
        _tt_model, _tt_index, _tt_item_ids = train_two_tower(epochs=5)
        status = "success" if _tt_index is not None else "skipped (not enough data)"
        return jsonify({"status": status})
    except Exception as e:
        logger.error(f"Erreur retrain : {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    logger.info(f"Démarrage du moteur IA sur le port {FLASK_PORT}")
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)