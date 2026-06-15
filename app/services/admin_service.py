"""Administravimo srities verslo logika."""

import csv
import io
from dataclasses import dataclass

from sqlalchemy import case, delete, func, or_, select
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Answer, ChecklistItem, Platform, Question, Session


@dataclass(frozen=True)
class DashboardStats:
    platforms: int
    questions: int
    recommendations: int
    sessions: int
    completed_sessions: int

    @property
    def completion_rate(self) -> int:
        if not self.sessions:
            return 0
        return round(self.completed_sessions / self.sessions * 100)


@dataclass(frozen=True)
class PlatformReportRow:
    name: str
    sessions: int
    completed: int

    @property
    def completion_rate(self) -> int:
        if not self.sessions:
            return 0
        return round(self.completed / self.sessions * 100)


class AdminService:
    def dashboard_stats(self) -> DashboardStats:
        return DashboardStats(
            platforms=self._count(Platform),
            questions=self._count(Question),
            recommendations=self._count(ChecklistItem),
            sessions=self._count(Session),
            completed_sessions=self._count(Session, Session.completed.is_(True)),
        )

    def platform_report(self) -> list[PlatformReportRow]:
        stmt = (
            select(
                Platform.name,
                func.count(Session.id),
                func.sum(case((Session.completed.is_(True), 1), else_=0)),
            )
            .outerjoin(Session, Session.platform_id == Platform.id)
            .group_by(Platform.id, Platform.name)
            .order_by(Platform.name)
        )
        return [
            PlatformReportRow(name=name, sessions=sessions or 0, completed=completed or 0)
            for name, sessions, completed in db.session.execute(stmt)
        ]

    def recent_sessions(self, limit: int = 10) -> list[Session]:
        stmt = (
            select(Session)
            .options(joinedload(Session.platform))
            .order_by(Session.started_at.desc())
            .limit(limit)
        )
        return list(db.session.execute(stmt).scalars())

    def list_questions(self, search: str = "", platform_code: str = "") -> list[Question]:
        stmt = select(Question).options(
            joinedload(Question.platform),
            joinedload(Question.answers),
        )
        if search:
            stmt = stmt.where(Question.text.ilike(f"%{search}%"))
        if platform_code:
            stmt = stmt.join(Question.platform).where(Platform.code == platform_code)
        stmt = stmt.order_by(Question.platform_id, Question.order_num)
        return list(db.session.execute(stmt).unique().scalars())

    def get_question(self, question_id: int) -> Question | None:
        stmt = (
            select(Question)
            .where(Question.id == question_id)
            .options(joinedload(Question.platform), joinedload(Question.answers))
        )
        return db.session.execute(stmt).unique().scalar_one_or_none()

    def create_question(
        self,
        platform_code: str,
        text: str,
        q_type: str,
        risk_areas: list[str],
    ) -> Question:
        platform = self._platform(platform_code)
        max_order = db.session.scalar(
            select(func.max(Question.order_num)).where(Question.platform_id == platform.id)
        )
        question = Question(
            platform_id=platform.id,
            text=text,
            q_type=q_type,
            order_num=(max_order or 0) + 1,
            risk_areas=risk_areas,
        )
        db.session.add(question)
        db.session.commit()
        return question

    def update_question(
        self,
        question: Question,
        text: str,
        q_type: str,
        risk_areas: list[str],
    ) -> None:
        self._invalidate_sessions(question.platform_id)
        question.text = text
        question.q_type = q_type
        question.risk_areas = risk_areas
        db.session.commit()

    def delete_question(self, question: Question) -> None:
        platform_id = question.platform_id
        self._invalidate_sessions(platform_id)
        db.session.delete(question)
        db.session.flush()
        self._renumber_questions(platform_id)
        db.session.commit()

    def create_answer(self, question: Question, text: str, risk_weight: int) -> None:
        self._invalidate_sessions(question.platform_id)
        max_order = db.session.scalar(
            select(func.max(Answer.order_num)).where(Answer.question_id == question.id)
        )
        db.session.add(
            Answer(
                question_id=question.id,
                text=text,
                risk_weight=risk_weight,
                order_num=(max_order or -1) + 1,
            )
        )
        db.session.commit()

    def update_answer(self, answer: Answer, text: str, risk_weight: int) -> None:
        self._invalidate_sessions(answer.question.platform_id)
        answer.text = text
        answer.risk_weight = risk_weight
        db.session.commit()

    def delete_answer(self, answer: Answer) -> None:
        question_id = answer.question_id
        platform_id = answer.question.platform_id
        self._invalidate_sessions(platform_id)
        db.session.delete(answer)
        db.session.flush()
        self._renumber_answers(question_id)
        db.session.commit()

    def get_answer(self, answer_id: int) -> Answer | None:
        stmt = select(Answer).where(Answer.id == answer_id).options(joinedload(Answer.question))
        return db.session.execute(stmt).scalar_one_or_none()

    def list_checklist_items(
        self,
        search: str = "",
        platform_code: str = "",
        risk_area: str = "",
    ) -> list[ChecklistItem]:
        stmt = select(ChecklistItem).options(joinedload(ChecklistItem.platform))
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    ChecklistItem.title.ilike(pattern),
                    ChecklistItem.description.ilike(pattern),
                )
            )
        if platform_code:
            stmt = stmt.join(ChecklistItem.platform).where(Platform.code == platform_code)
        if risk_area:
            stmt = stmt.where(ChecklistItem.risk_area == risk_area)
        stmt = stmt.order_by(ChecklistItem.platform_id, ChecklistItem.priority)
        return list(db.session.execute(stmt).scalars())

    def get_checklist_item(self, item_id: int) -> ChecklistItem | None:
        stmt = (
            select(ChecklistItem)
            .where(ChecklistItem.id == item_id)
            .options(joinedload(ChecklistItem.platform))
        )
        return db.session.execute(stmt).scalar_one_or_none()

    def create_checklist_item(
        self,
        platform_code: str,
        title: str,
        description: str,
        priority: int,
        risk_area: str,
        when_specialist: str | None,
    ) -> ChecklistItem:
        platform = self._platform(platform_code)
        item = ChecklistItem(
            platform_id=platform.id,
            title=title,
            description=description,
            priority=priority,
            risk_area=risk_area,
            when_specialist=when_specialist,
            trigger_answer_ids=[],
        )
        db.session.add(item)
        db.session.commit()
        return item

    def update_checklist_item(
        self,
        item: ChecklistItem,
        platform_code: str,
        title: str,
        description: str,
        priority: int,
        risk_area: str,
        when_specialist: str | None,
    ) -> None:
        platform = self._platform(platform_code)
        item.platform_id = platform.id
        item.title = title
        item.description = description
        item.priority = priority
        item.risk_area = risk_area
        item.when_specialist = when_specialist
        db.session.commit()

    def delete_checklist_item(self, item: ChecklistItem) -> None:
        db.session.delete(item)
        db.session.commit()

    def report_csv(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Platforma", "Sesijos", "Užbaigtos", "Užbaigimas (%)"])
        for row in self.platform_report():
            writer.writerow([row.name, row.sessions, row.completed, row.completion_rate])
        return output.getvalue()

    @staticmethod
    def _count(model: type, *conditions: object) -> int:
        stmt = select(func.count()).select_from(model)
        if conditions:
            stmt = stmt.where(*conditions)
        return db.session.scalar(stmt) or 0

    @staticmethod
    def _platform(code: str) -> Platform:
        platform = db.session.scalar(select(Platform).where(Platform.code == code))
        if not platform:
            raise ValueError("Platforma nerasta")
        return platform

    @staticmethod
    def _invalidate_sessions(platform_id: int) -> None:
        db.session.execute(delete(Session).where(Session.platform_id == platform_id))
        db.session.flush()

    @staticmethod
    def _renumber_questions(platform_id: int) -> None:
        questions = list(
            db.session.scalars(
                select(Question)
                .where(Question.platform_id == platform_id)
                .order_by(Question.order_num)
            )
        )
        for index, question in enumerate(questions, start=1):
            question.order_num = index + 1000
        db.session.flush()
        for index, question in enumerate(questions, start=1):
            question.order_num = index

    @staticmethod
    def _renumber_answers(question_id: int) -> None:
        answers = list(
            db.session.scalars(
                select(Answer).where(Answer.question_id == question_id).order_by(Answer.order_num)
            )
        )
        for index, answer in enumerate(answers):
            answer.order_num = index
