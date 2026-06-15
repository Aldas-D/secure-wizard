"""Server-rendered klausimyno maršrutai."""

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
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

bp = Blueprint("quiz", __name__)
logger = get_logger(__name__)


@bp.route("/start", methods=["GET", "POST"])
@limiter.limit("20 per minute")
def start():
    if request.method == "POST":
        try:
            choice = PlatformChoice(platform=request.form.get("platform", ""))
        except ValidationError as e:
            logger.warning("invalid_platform", error=str(e))
            flash("Pasirinkite galiojančią platformą", "error")
            return redirect(url_for("quiz.start"))

        service = SessionService()
        session, raw_token = service.create_session(choice.platform)
        logger.info("session_created", session_id=session.id, platform=choice.platform)
        return redirect(url_for("quiz.question", token=raw_token))

    platforms = QuestionRepository.get_all_platforms()
    return render_template("quiz/platform_select.html", platforms=platforms)


@bp.route("/<string:token>/question", methods=["GET"])
def question(token: str):
    try:
        session = SessionService().get_active_session(token)
    except SessionNotFoundError:
        flash("Sesija nerasta. Pradėkite iš naujo.", "error")
        return redirect(url_for("quiz.start"))
    except SessionExpiredError:
        flash("Sesijos laikas baigėsi. Pradėkite iš naujo.", "warning")
        return redirect(url_for("quiz.start"))

    quiz_service = QuizService()
    ctx = quiz_service.get_current_question(session)

    if ctx is None:
        return redirect(url_for("quiz.result", token=token))

    return render_template("quiz/question.html", ctx=ctx, token=token)


@bp.route("/<string:token>/answer", methods=["POST"])
@limiter.limit("60 per minute")
def submit_answer(token: str):
    try:
        session = SessionService().get_active_session(token)
    except (SessionNotFoundError, SessionExpiredError):
        return redirect(url_for("quiz.start"))

    answer_ids_raw = request.form.getlist("answer_id")
    try:
        submission = AnswerSubmission(
            question_id=int(request.form.get("question_id", 0)),
            answer_ids=[int(a) for a in answer_ids_raw if a],
        )
    except (TypeError, ValueError, ValidationError):
        flash("Patikrinkite pasirinkimą", "error")
        return redirect(url_for("quiz.question", token=token))

    try:
        QuizService().submit_answer(session, submission.question_id, submission.answer_ids)
    except InvalidAnswerError as e:
        logger.warning("invalid_answer", session_id=session.id, error=str(e))
        flash("Atsakymas netinkamas", "error")
        return redirect(url_for("quiz.question", token=token))

    return redirect(url_for("quiz.question", token=token))


@bp.route("/<string:token>/back", methods=["POST"])
@limiter.limit("30 per minute")
def go_back(token: str):
    try:
        session = SessionService().get_active_session(token)
    except (SessionNotFoundError, SessionExpiredError):
        return redirect(url_for("quiz.start"))

    SessionService().go_back(session)
    return redirect(url_for("quiz.question", token=token))


@bp.route("/<string:token>/result", methods=["GET"])
def result(token: str):
    try:
        session = SessionService().get_active_session(token)
    except (SessionNotFoundError, SessionExpiredError):
        flash("Sesija negalioja", "error")
        return redirect(url_for("quiz.start"))

    plan = QuizService().generate_result(session)
    return render_template("quiz/result.html", plan=plan, token=token)
