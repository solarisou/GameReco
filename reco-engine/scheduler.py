"""
scheduler.py — Réentraînement automatique du moteur hybride (SVD + TF-IDF + Two-Tower).

Utilise APScheduler pour déclencher retrain() toutes les RETRAIN_INTERVAL_HOURS heures.
Désactivation : mettre AUTO_RETRAIN=false dans .env
"""

from apscheduler.schedulers.background import BackgroundScheduler
from utils import logger, RETRAIN_INTERVAL_HOURS, AUTO_RETRAIN


def start_scheduler(engine) -> BackgroundScheduler | None:
    if not AUTO_RETRAIN:
        logger.info("Réentraînement automatique désactivé (AUTO_RETRAIN=false)")
        return None

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func             = engine.retrain,
        trigger          = "interval",
        hours            = RETRAIN_INTERVAL_HOURS,
        id               = "auto_retrain",
        name             = "Réentraînement SVD + TF-IDF + Two-Tower",
        replace_existing = True
    )
    scheduler.start()
    logger.info(f"Scheduler démarré — réentraînement toutes les {RETRAIN_INTERVAL_HOURS}h")
    return scheduler