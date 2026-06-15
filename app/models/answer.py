"""Atsakymo variantas."""

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Answer(db.Model):
    __tablename__ = "answer"
    __table_args__ = (CheckConstraint("risk_weight BETWEEN 0 AND 10", name="ck_risk_weight_range"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(db.Text, nullable=False)
    risk_weight: Mapped[int] = mapped_column(nullable=False)
    order_num: Mapped[int] = mapped_column(nullable=False, default=0)

    question = relationship("Question", back_populates="answers")

    def __repr__(self) -> str:
        return f"<Answer {self.id} weight={self.risk_weight}>"
