"""Patikros plano veiksmas."""

from sqlalchemy import JSON, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class ChecklistItem(db.Model):
    __tablename__ = "checklist_item"
    __table_args__ = (
        CheckConstraint("priority BETWEEN 1 AND 5", name="ck_priority_range"),
        db.Index("idx_checklist_platform_risk", "platform_id", "risk_area"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[int] = mapped_column(
        ForeignKey("platform.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    description: Mapped[str] = mapped_column(db.Text, nullable=False)
    priority: Mapped[int] = mapped_column(nullable=False)
    risk_area: Mapped[str] = mapped_column(db.String(10), nullable=False)
    when_specialist: Mapped[str | None] = mapped_column(db.Text)
    trigger_answer_ids: Mapped[list[int]] = mapped_column(JSON, nullable=False, default=list)

    platform = relationship("Platform", back_populates="checklist_items")

    def __repr__(self) -> str:
        return f"<ChecklistItem {self.id} priority={self.priority}>"
