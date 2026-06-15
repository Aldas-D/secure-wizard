"""Secure Wizard JSON API."""

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.extensions import limiter
from app.logging_config import get_logger
from app.repositories import QuestionRepository
from app.schemas.quiz import AnswerSubmission, PlatformChoice
from app.services.quiz_service import InvalidAnswerError, QuizService
from app.services.session_service import (
    SessionExpiredError,
    SessionNotFoundError,
    SessionService,
)

bp = Blueprint("api", __name__)
logger = get_logger(__name__)


def _serialize_question(question, current_step: int, total: int) -> dict:
    return {
        "id": question.id,
        "text": question.text,
        "type": question.q_type,
        "answers": [{"id": a.id, "text": a.text} for a in question.answers],
        "current_step": current_step,
        "total_questions": total,
    }


def _validation_error_response(e: ValidationError):
    errors = e.errors(include_url=False, include_context=False)
    logger.warning("api_validation_error", errors=errors)
    return jsonify({"error": "validation_error", "message": "Neteisingi įvesties duomenys"}), 422


@bp.route("/platforms", methods=["GET"])
@limiter.limit("60 per minute")
def platforms():
    items = QuestionRepository.get_all_platforms()
    return jsonify(
        {
            "platforms": [
                {"code": p.code, "name": p.name, "description": p.description} for p in items
            ]
        }
    )


@bp.route("/sessions", methods=["POST"])
@limiter.limit("20 per minute")
def create_session():
    try:
        choice = PlatformChoice.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return _validation_error_response(e)

    service = SessionService()
    quiz = QuizService()
    try:
        session, raw_token = service.create_session(choice.platform)
    except ValueError:
        return jsonify({"error": "platform_not_found"}), 404
    ctx = quiz.get_current_question(session)

    return jsonify(
        {
            "token": raw_token,
            "platform": choice.platform,
            "current_step": 0,
            "first_question": _serialize_question(
                ctx.question, ctx.current_step, ctx.total_questions
            )
            if ctx
            else None,
        }
    ), 201


@bp.route("/sessions/<string:token>", methods=["GET"])
@limiter.limit("60 per minute")
def get_session(token: str):
    try:
        session = SessionService().get_active_session(token)
    except SessionNotFoundError:
        return jsonify({"error": "session_not_found"}), 404
    except SessionExpiredError:
        return jsonify({"error": "session_expired"}), 410

    ctx = QuizService().get_current_question(session)
    return jsonify(
        {
            "current_step": session.current_step,
            "completed": session.completed,
            "current_question": _serialize_question(
                ctx.question, ctx.current_step, ctx.total_questions
            )
            if ctx
            else None,
        }
    )


@bp.route("/sessions/<string:token>/answer", methods=["POST"])
@limiter.limit("60 per minute")
def submit_answer(token: str):
    try:
        session = SessionService().get_active_session(token)
    except SessionNotFoundError:
        return jsonify({"error": "session_not_found"}), 404
    except SessionExpiredError:
        return jsonify({"error": "session_expired"}), 410

    try:
        submission = AnswerSubmission.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return _validation_error_response(e)

    quiz = QuizService()
    try:
        quiz.submit_answer(session, submission.question_id, submission.answer_ids)
    except InvalidAnswerError as e:
        logger.warning("api_invalid_answer", session_id=session.id, error=str(e))
        return jsonify({"error": "invalid_answer"}), 400

    ctx = quiz.get_current_question(session)
    if ctx is None:
        return jsonify(
            {
                "current_step": session.current_step,
                "completed": True,
                "result_url": f"/quiz/{token}/result",
            }
        )

    return jsonify(
        {
            "current_step": ctx.current_step,
            "total_questions": ctx.total_questions,
            "next_question": _serialize_question(
                ctx.question, ctx.current_step, ctx.total_questions
            ),
        }
    )


@bp.route("/sessions/<string:token>/result", methods=["GET"])
@limiter.limit("30 per minute")
def get_result(token: str):
    try:
        session = SessionService().get_active_session(token)
    except SessionNotFoundError:
        return jsonify({"error": "session_not_found"}), 404
    except SessionExpiredError:
        return jsonify({"error": "session_expired"}), 410

    plan = QuizService().generate_result(session)
    return jsonify(
        {
            "profile": {
                "total_score": plan.profile.total_score,
                "max_score": plan.profile.max_score,
                "level": plan.profile.level.value,
                "level_display": plan.profile.level.display_name,
                "percentage": plan.profile.percentage,
                "areas": plan.profile.areas,
            },
            "items": [item.model_dump() for item in plan.items],
            "generated_at": plan.generated_at,
        }
    )
