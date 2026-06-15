"""Vartotojo sesija ir jos atsakymai."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Session(db.Model):
    __tablename__ = "session"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Duomenų bazėje laikoma tik SHA-256 sesijos žetono santrauka.
    token_hash: Mapped[str] = mapped_column(db.String(64), unique=True, nullable=False, index=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platform.id"), nullable=False)
    current_step: Mapped[int] = mapped_column(default=0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    completed: Mapped[bool] = mapped_column(default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column()

    platform = relationship("Platform")
    answers = relationship(
        "SessionAnswer",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionAnswer.answered_at",
    )

    def touch(self) -> None:
        """Atnaujinti aktyvumo laiką."""
        self.last_active_at = datetime.now(UTC)

    def is_expired(self, lifetime_minutes: int) -> bool:
        cutoff = datetime.now(UTC) - timedelta(minutes=lifetime_minutes)
        last_active = self.last_active_at
        if last_active.tzinfo is None:
            last_active = last_active.replace(tzinfo=UTC)
        return last_active < cutoff

    def __repr__(self) -> str:
        return f"<Session id={self.id} step={self.current_step}>"


class SessionAnswer(db.Model):
    __tablename__ = "session_answer"
    __table_args__ = (
        UniqueConstraint("session_id", "question_id", "answer_id", name="uq_session_qa"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("session.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[int] = mapped_column(ForeignKey("question.id"), nullable=False)
    answer_id: Mapped[int] = mapped_column(ForeignKey("answer.id"), nullable=False)
    answered_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)

    session = relationship("Session", back_populates="answers")
    question = relationship("Question")
    answer = relationship("Answer")
