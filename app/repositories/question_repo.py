"""Klausimų ir platformų užklausos."""

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Platform, Question


class QuestionRepository:
    @staticmethod
    def get_platform_by_code(code: str) -> Platform | None:
        stmt = select(Platform).where(Platform.code == code.upper())
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_all_platforms() -> list[Platform]:
        return list(db.session.execute(select(Platform)).scalars().all())

    @staticmethod
    def find_by_platform_ordered(platform_id: int) -> list[Question]:
        stmt = (
            select(Question)
            .where(Question.platform_id == platform_id)
            .options(joinedload(Question.answers))
            .order_by(Question.order_num)
        )
        return list(db.session.execute(stmt).unique().scalars().all())

    @staticmethod
    def get_question_by_order(platform_id: int, order_num: int) -> Question | None:
        stmt = (
            select(Question)
            .where(Question.platform_id == platform_id, Question.order_num == order_num)
            .options(joinedload(Question.answers))
        )
        return db.session.execute(stmt).unique().scalar_one_or_none()

    @staticmethod
    def count_by_platform(platform_id: int) -> int:
        stmt = select(db.func.count(Question.id)).where(Question.platform_id == platform_id)
        return db.session.execute(stmt).scalar_one() or 0
