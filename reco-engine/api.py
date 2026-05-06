from flask import Flask, request, jsonify
from hybrid_engine import HybridEngine
from utils import logger, FLASK_PORT

app = Flask(__name__)

# Initialisation unique du moteur au démarrage
engine = HybridEngine()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "reco-engine"})


@app.route("/recommend", methods=["POST"])
def recommend():
    """
    Body JSON attendu :
    {
        "user_id": "uuid",
        "type": "manga" | "game" | null,
        "top_n": 10
    }
    """
    data    = request.get_json()
    user_id = data.get("user_id")
    item_type = data.get("type")       # optionnel
    top_n   = int(data.get("top_n", 10))

    if not user_id:
        return jsonify({"error": "user_id requis"}), 400

    try:
        results = engine.recommend(user_id, item_type, top_n)
        return jsonify({"user_id": user_id, "recommendations": results})
    except Exception as e:
        logger.error(f"Erreur recommend : {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    logger.info(f"Démarrage du moteur IA sur le port {FLASK_PORT}")
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)
