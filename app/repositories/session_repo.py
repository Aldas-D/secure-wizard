"""Sesijų užklausos."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Session, SessionAnswer


class SessionRepository:
    @staticmethod
    def create(token_hash: str, platform_id: int) -> Session:
        session = Session(token_hash=token_hash, platform_id=platform_id, current_step=0)
        db.session.add(session)
        db.session.flush()
        return session

    @staticmethod
    def find_by_token_hash(token_hash: str) -> Session | None:
        stmt = (
            select(Session)
            .where(Session.token_hash == token_hash)
            .options(joinedload(Session.platform))
        )
        return db.session.execute(stmt).unique().scalar_one_or_none()

    @staticmethod
    def find_with_answers(token_hash: str) -> Session | None:
        stmt = (
            select(Session)
            .where(Session.token_hash == token_hash)
            .options(
                joinedload(Session.platform),
                joinedload(Session.answers).joinedload(SessionAnswer.answer),
                joinedload(Session.answers).joinedload(SessionAnswer.question),
            )
        )
        return db.session.execute(stmt).unique().scalar_one_or_none()

    @staticmethod
    def find_with_answers_by_id(session_id: int) -> Session | None:
        stmt = (
            select(Session)
            .where(Session.id == session_id)
            .options(
                joinedload(Session.platform),
                joinedload(Session.answers).joinedload(SessionAnswer.answer),
                joinedload(Session.answers).joinedload(SessionAnswer.question),
            )
        )
        return db.session.execute(stmt).unique().scalar_one_or_none()

    @staticmethod
    def save_answer(session_id: int, question_id: int, answer_id: int) -> None:
        sa = SessionAnswer(session_id=session_id, question_id=question_id, answer_id=answer_id)
        db.session.add(sa)

    @staticmethod
    def delete_answers_for_question(session_id: int, question_id: int) -> None:
        stmt = delete(SessionAnswer).where(
            SessionAnswer.session_id == session_id,
            SessionAnswer.question_id == question_id,
        )
        db.session.execute(stmt)

    @staticmethod
    def cleanup_expired(lifetime_minutes: int) -> int:
        cutoff = datetime.now(UTC) - timedelta(minutes=lifetime_minutes)
        stmt = delete(Session).where(Session.last_active_at < cutoff)
        result = db.session.execute(stmt)
        return result.rowcount or 0
