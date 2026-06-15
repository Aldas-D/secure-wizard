"""Sesijų valdymas."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from flask import current_app

from app.extensions import db
from app.models import Session
from app.repositories import QuestionRepository, SessionRepository

_TOUCH_INTERVAL = timedelta(seconds=30)
_TOKEN_BYTES = 32


class SessionExpiredError(Exception):
    pass


class SessionNotFoundError(Exception):
    pass


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class SessionService:
    def __init__(self) -> None:
        self.repo = SessionRepository()
        self.question_repo = QuestionRepository()

    def create_session(self, platform_code: str) -> tuple[Session, str]:
        platform = self.question_repo.get_platform_by_code(platform_code)
        if not platform:
            raise ValueError(f"Nežinoma platforma: {platform_code}")

        raw_token = secrets.token_urlsafe(_TOKEN_BYTES)
        token_hash = hash_token(raw_token)

        session = self.repo.create(token_hash=token_hash, platform_id=platform.id)
        db.session.commit()
        return session, raw_token

    def get_active_session(self, raw_token: str) -> Session:
        if not raw_token or len(raw_token) > 200:
            raise SessionNotFoundError("Sesija nerasta")

        token_hash = hash_token(raw_token)
        session = self.repo.find_by_token_hash(token_hash)
        if not session:
            raise SessionNotFoundError("Sesija nerasta")

        lifetime = current_app.config["QUIZ_SESSION_LIFETIME_MIN"]
        if session.is_expired(lifetime):
            raise SessionExpiredError("Sesijos laikas baigėsi")

        self._throttled_touch(session)
        return session

    def get_session_with_answers(self, raw_token: str) -> Session:
        token_hash = hash_token(raw_token)
        session = self.repo.find_with_answers(token_hash)
        if not session:
            raise SessionNotFoundError("Sesija nerasta")
        return session

    def get_session_with_answers_by_id(self, session_id: int) -> Session:
        session = self.repo.find_with_answers_by_id(session_id)
        if not session:
            raise SessionNotFoundError("Sesija nerasta")
        return session

    def advance_step(self, session: Session) -> None:
        session.current_step += 1
        session.touch()
        db.session.commit()

    def go_back(self, session: Session) -> None:
        if session.current_step > 0:
            current_question = self.question_repo.get_question_by_order(
                session.platform_id, session.current_step
            )
            if current_question:
                self.repo.delete_answers_for_question(session.id, current_question.id)
            session.current_step -= 1
            session.touch()
            db.session.commit()

    def complete(self, session: Session) -> None:
        session.completed = True
        session.completed_at = datetime.now(UTC)
        db.session.commit()

    def _throttled_touch(self, session: Session) -> None:
        now = datetime.now(UTC)
        last_active = session.last_active_at
        if last_active.tzinfo is None:
            last_active = last_active.replace(tzinfo=UTC)
        if now - last_active >= _TOUCH_INTERVAL:
            session.touch()
            db.session.commit()
