"""Klausimas."""

from datetime import UTC, datetime

from sqlalchemy import JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Question(db.Model):
    __tablename__ = "question"
    __table_args__ = (
        UniqueConstraint("platform_id", "order_num", name="uq_platform_order"),
        db.Index("idx_question_platform_order", "platform_id", "order_num"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[int] = mapped_column(
        ForeignKey("platform.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(db.Text, nullable=False)
    q_type: Mapped[str] = mapped_column(db.String(10), nullable=False)
    order_num: Mapped[int] = mapped_column(nullable=False)
    risk_areas: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    platform = relationship("Platform", back_populates="questions")
    answers = relationship(
        "Answer",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="Answer.order_num",
    )

    def __repr__(self) -> str:
        return f"<Question {self.id} order={self.order_num}>"
