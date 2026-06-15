"""Patikros veiksmų užklausos."""

from sqlalchemy import select

from app.extensions import db
from app.models import ChecklistItem


class ChecklistRepository:
    @staticmethod
    def find_by_platform(platform_id: int) -> list[ChecklistItem]:
        stmt = (
            select(ChecklistItem)
            .where(ChecklistItem.platform_id == platform_id)
            .order_by(ChecklistItem.priority)
        )
        return list(db.session.execute(stmt).scalars().all())
