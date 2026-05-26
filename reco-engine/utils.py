import os
import logging

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger("reco-engine")

# ── Config base de données ────────────────────────────────────
DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_PORT     = os.getenv("DB_PORT",     "3306")
DB_NAME     = os.getenv("DB_NAME",     "ter_reco")
DB_USER     = os.getenv("DB_USER",     "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")

FLASK_PORT  = int(os.getenv("FLASK_PORT", 5000))

# ── Poids de fusion hybride ───────────────────────────────────
# Les trois poids doivent sommer à 1.0
# Si Two-Tower non disponible (cold start / pas assez de data),
# SVD et Content se partagent automatiquement le poids restant.
HYBRID_COLLAB_WEIGHT     = float(os.getenv("HYBRID_COLLAB_WEIGHT",     "0.5"))
HYBRID_CONTENT_WEIGHT    = float(os.getenv("HYBRID_CONTENT_WEIGHT",    "0.3"))
HYBRID_TWOTOWER_WEIGHT   = float(os.getenv("HYBRID_TWOTOWER_WEIGHT",   "0.2"))

# Nombre de recommandations retournées par défaut
TOP_N = int(os.getenv("TOP_N", "10"))

# ── Réentraînement automatique ────────────────────────────────
AUTO_RETRAIN           = os.getenv("AUTO_RETRAIN", "true").lower() == "true"
RETRAIN_INTERVAL_HOURS = int(os.getenv("RETRAIN_INTERVAL_HOURS", "6"))

# ── Two-Tower ─────────────────────────────────────────────────
TWOTOWER_EPOCHS     = int(os.getenv("TWOTOWER_EPOCHS",     "5"))
TWOTOWER_BATCH_SIZE = int(os.getenv("TWOTOWER_BATCH_SIZE", "64"))
TWOTOWER_EMB_DIM    = int(os.getenv("TWOTOWER_EMB_DIM",    "32"))