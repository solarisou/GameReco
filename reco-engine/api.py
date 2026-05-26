from flask import Flask, request, jsonify
from hybrid_engine import HybridEngine
from scheduler import start_scheduler
from utils import logger, FLASK_PORT

app = Flask(__name__)

engine    = HybridEngine()
scheduler = start_scheduler(engine)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "reco-engine"})


@app.route("/recommend", methods=["POST"])
def recommend():
    data      = request.get_json()
    user_id   = data.get("user_id")
    item_type = data.get("type")
    top_n     = int(data.get("top_n", 10))

    if not user_id:
        return jsonify({"error": "user_id requis"}), 400

    try:
        results = engine.recommend(user_id, item_type, top_n)
        return jsonify({"user_id": user_id, "recommendations": results})
    except Exception as e:
        logger.error(f"Erreur recommend : {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/retrain", methods=["POST"])
def retrain():
    """
    Déclenche manuellement un réentraînement complet
    (SVD + KNN + TF-IDF + Two-Tower).
    Retourne 409 si un entraînement est déjà en cours.
    """
    if engine.get_status()["is_training"]:
        return jsonify({
            "message": "Réentraînement déjà en cours",
            "status":  engine.get_status()
        }), 409

    started = engine.retrain()
    code    = 202 if started else 500
    return jsonify({
        "message": "Réentraînement démarré (SVD + TF-IDF + Two-Tower)" if started
                   else "Impossible de démarrer",
        "status":  engine.get_status()
    }), code


@app.route("/retrain/status", methods=["GET"])
def retrain_status():
    """
    Retourne l'état courant :
    {
        "is_training": false,
        "last_trained": "2026-05-20T17:00:00",
        "trained_on": { "ratings": 1250, "items": 498 },
        "two_tower": "ready"   // "disabled" | "training" | "ready"
    }
    """
    return jsonify(engine.get_status())


if __name__ == "__main__":
    logger.info(f"Démarrage du moteur IA sur le port {FLASK_PORT}")
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)