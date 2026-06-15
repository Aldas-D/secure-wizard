"""Periodinis pasenusių sesijų valymas."""

import time

from app import create_app
from app.extensions import db
from app.logging_config import get_logger
from app.repositories import SessionRepository

logger = get_logger(__name__)


def cleanup_loop(interval_seconds: int = 3600) -> None:
    app = create_app()
    while True:
        try:
            with app.app_context():
                deleted = SessionRepository.cleanup_expired(app.config["QUIZ_SESSION_LIFETIME_MIN"])
                db.session.commit()
                logger.info("sessions_cleaned", deleted_count=deleted)
        except Exception:
            logger.exception("cleanup_failed")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    cleanup_loop()
