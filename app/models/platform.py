"""Platforma: Windows arba Android."""

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Platform(db.Model):
    __tablename__ = "platform"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(db.String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(db.String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(db.Text)

    questions = relationship("Question", back_populates="platform", cascade="all, delete-orphan")
    checklist_items = relationship(
        "ChecklistItem", back_populates="platform", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Platform {self.code}>"
