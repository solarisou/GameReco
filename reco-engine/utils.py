from dotenv import load_dotenv
load_dotenv()

import os
import logging

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger("reco-engine")

# ── Config ───────────────────────────────────────────────────
DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_PORT     = os.getenv("DB_PORT",     "3306")
DB_NAME     = os.getenv("DB_NAME",     "ter_reco")
DB_USER     = os.getenv("DB_USER",     "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")

FLASK_PORT  = int(os.getenv("FLASK_PORT", 5000))

# Poids de fusion hybride (collaboratif vs contenu)
HYBRID_COLLAB_WEIGHT  = float(os.getenv("HYBRID_COLLAB_WEIGHT",  "0.6"))
HYBRID_CONTENT_WEIGHT = float(os.getenv("HYBRID_CONTENT_WEIGHT", "0.4"))

# Nombre de recommandations retournées par défaut
TOP_N = int(os.getenv("TOP_N", "10"))


# ── IGDB ─────────────────────────────────────────────────────
IGDB_CLIENT_ID     = os.getenv("IGDB_CLIENT_ID",     "")
IGDB_CLIENT_SECRET = os.getenv("IGDB_CLIENT_SECRET", "")