"""Klausimyno eiga ir atsakymų išsaugojimas."""

from dataclasses import dataclass

from app.extensions import db
from app.models import Question, Session
from app.repositories import QuestionRepository, SessionRepository
from app.services.plan_generator import PlanGenerator
from app.services.risk_engine import RiskEngine
from app.services.session_service import SessionService


@dataclass
class QuestionContext:
    question: Question
    current_step: int
    total_questions: int

    @property
    def progress_pct(self) -> int:
        return round(self.current_step / self.total_questions * 100) if self.total_questions else 0

    @property
    def is_last(self) -> bool:
        return self.current_step >= self.total_questions


class InvalidAnswerError(Exception):
    pass


class QuizService:
    def __init__(self) -> None:
        self.question_repo = QuestionRepository()
        self.session_repo = SessionRepository()
        self.session_service = SessionService()
        self.risk_engine = RiskEngine()
        self.plan_generator = PlanGenerator()

    def get_current_question(self, session: Session) -> QuestionContext | None:
        total = self.question_repo.count_by_platform(session.platform_id)
        next_order = session.current_step + 1

        if next_order > total:
            return None

        question = self.question_repo.get_question_by_order(session.platform_id, next_order)
        if not question:
            return None

        return QuestionContext(question=question, current_step=next_order, total_questions=total)

    def submit_answer(self, session: Session, question_id: int, answer_ids: list[int]) -> None:
        expected_question = self.question_repo.get_question_by_order(
            session.platform_id, session.current_step + 1
        )
        if not expected_question or expected_question.id != question_id:
            raise InvalidAnswerError("Klausimas neatitinka dabartinio žingsnio")

        valid_answer_ids = {a.id for a in expected_question.answers}
        if not set(answer_ids).issubset(valid_answer_ids):
            raise InvalidAnswerError("Atsakymai neatitinka klausimo")

        if expected_question.q_type == "single" and len(answer_ids) != 1:
            raise InvalidAnswerError("Vienam pasirinkimo klausimui reikalingas vienas atsakymas")

        try:
            with db.session.begin_nested():
                self.session_repo.delete_answers_for_question(session.id, question_id)
                for answer_id in answer_ids:
                    self.session_repo.save_answer(session.id, question_id, answer_id)
            self.session_service.advance_step(session)
        except Exception:
            db.session.rollback()
            raise

    def generate_result(self, session: Session):
        session_with_answers = self.session_service.get_session_with_answers_by_id(session.id)

        profile = self.risk_engine.calculate(session_with_answers.answers)
        plan = self.plan_generator.generate(
            platform_id=session.platform_id,
            profile=profile,
            session_answers=session_with_answers.answers,
        )

        if not session.completed:
            self.session_service.complete(session)

        return plan
