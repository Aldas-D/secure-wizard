"""Administratoriaus prisijungimas, CRUD ir ataskaitos."""

import hmac

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from app.auth import admin_required
from app.extensions import limiter
from app.repositories import QuestionRepository
from app.services.admin_service import AdminService

bp = Blueprint("admin", __name__)

RISK_AREAS = {
    "PWD": "Slaptažodžiai",
    "UPD": "Atnaujinimai",
    "APP": "Programėlės",
    "NET": "Tinklas",
    "ACC": "Paskyros",
}


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        expected_username = current_app.config["ADMIN_USERNAME"]
        password_hash = current_app.config["ADMIN_PASSWORD_HASH"]

        valid_username = hmac.compare_digest(username, expected_username)
        try:
            valid_password = bool(password_hash) and check_password_hash(password_hash, password)
        except ValueError:
            valid_password = False
        if valid_username and valid_password:
            session.clear()
            session["admin_authenticated"] = True
            session["admin_username"] = username
            flash("Prisijungta prie administravimo srities", "success")
            return redirect(url_for("admin.dashboard"))

        flash("Neteisingas naudotojo vardas arba slaptažodis", "error")

    return render_template("admin/login.html")


@bp.route("/logout", methods=["POST"])
@admin_required
def logout():
    session.clear()
    flash("Atsijungta", "success")
    return redirect(url_for("main.index"))


@bp.route("/")
@admin_required
def dashboard():
    service = AdminService()
    return render_template(
        "admin/dashboard.html",
        stats=service.dashboard_stats(),
        report=service.platform_report(),
        recent_sessions=service.recent_sessions(),
    )


@bp.route("/questions")
@admin_required
def questions():
    search = request.args.get("q", "").strip()
    platform = request.args.get("platform", "").strip().upper()
    return render_template(
        "admin/questions.html",
        questions=AdminService().list_questions(search, platform),
        platforms=QuestionRepository.get_all_platforms(),
        search=search,
        selected_platform=platform,
    )


@bp.route("/questions/new", methods=["GET", "POST"])
@admin_required
def question_new():
    if request.method == "POST":
        try:
            question = AdminService().create_question(
                platform_code=request.form["platform"],
                text=_required("text"),
                q_type=_question_type(),
                risk_areas=_risk_areas(),
            )
        except (KeyError, ValueError) as exc:
            flash(str(exc), "error")
        else:
            flash("Klausimas sukurtas. Dabar pridėkite atsakymus.", "success")
            return redirect(url_for("admin.question_edit", question_id=question.id))

    return render_template(
        "admin/question_form.html",
        question=None,
        platforms=QuestionRepository.get_all_platforms(),
        risk_areas=RISK_AREAS,
    )


@bp.route("/questions/<int:question_id>/edit", methods=["GET", "POST"])
@admin_required
def question_edit(question_id: int):
    service = AdminService()
    question = service.get_question(question_id)
    if not question:
        abort(404)

    if request.method == "POST":
        try:
            service.update_question(
                question,
                text=_required("text"),
                q_type=_question_type(),
                risk_areas=_risk_areas(),
            )
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            flash("Klausimas atnaujintas", "success")
            return redirect(url_for("admin.question_edit", question_id=question.id))

    return render_template(
        "admin/question_form.html",
        question=question,
        platforms=QuestionRepository.get_all_platforms(),
        risk_areas=RISK_AREAS,
    )


@bp.route("/questions/<int:question_id>/delete", methods=["POST"])
@admin_required
def question_delete(question_id: int):
    service = AdminService()
    question = service.get_question(question_id)
    if not question:
        abort(404)
    service.delete_question(question)
    flash("Klausimas ištrintas", "success")
    return redirect(url_for("admin.questions"))


@bp.route("/questions/<int:question_id>/answers", methods=["POST"])
@admin_required
def answer_new(question_id: int):
    service = AdminService()
    question = service.get_question(question_id)
    if not question:
        abort(404)
    try:
        service.create_answer(question, _required("answer_text"), _risk_weight())
    except ValueError as exc:
        flash(str(exc), "error")
    else:
        flash("Atsakymo variantas pridėtas", "success")
    return redirect(url_for("admin.question_edit", question_id=question_id))


@bp.route("/answers/<int:answer_id>/edit", methods=["POST"])
@admin_required
def answer_edit(answer_id: int):
    service = AdminService()
    answer = service.get_answer(answer_id)
    if not answer:
        abort(404)
    try:
        service.update_answer(answer, _required("answer_text"), _risk_weight())
    except ValueError as exc:
        flash(str(exc), "error")
    else:
        flash("Atsakymo variantas atnaujintas", "success")
    return redirect(url_for("admin.question_edit", question_id=answer.question_id))


@bp.route("/answers/<int:answer_id>/delete", methods=["POST"])
@admin_required
def answer_delete(answer_id: int):
    service = AdminService()
    answer = service.get_answer(answer_id)
    if not answer:
        abort(404)
    question_id = answer.question_id
    service.delete_answer(answer)
    flash("Atsakymo variantas ištrintas", "success")
    return redirect(url_for("admin.question_edit", question_id=question_id))


@bp.route("/recommendations")
@admin_required
def recommendations():
    search = request.args.get("q", "").strip()
    platform = request.args.get("platform", "").strip().upper()
    risk_area = request.args.get("risk_area", "").strip().upper()
    return render_template(
        "admin/recommendations.html",
        items=AdminService().list_checklist_items(search, platform, risk_area),
        platforms=QuestionRepository.get_all_platforms(),
        risk_areas=RISK_AREAS,
        search=search,
        selected_platform=platform,
        selected_risk_area=risk_area,
    )


@bp.route("/recommendations/new", methods=["GET", "POST"])
@admin_required
def recommendation_new():
    if request.method == "POST":
        try:
            AdminService().create_checklist_item(**_recommendation_form())
        except (KeyError, ValueError) as exc:
            flash(str(exc), "error")
        else:
            flash("Rekomendacija sukurta", "success")
            return redirect(url_for("admin.recommendations"))

    return render_template(
        "admin/recommendation_form.html",
        item=None,
        platforms=QuestionRepository.get_all_platforms(),
        risk_areas=RISK_AREAS,
    )


@bp.route("/recommendations/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def recommendation_edit(item_id: int):
    service = AdminService()
    item = service.get_checklist_item(item_id)
    if not item:
        abort(404)

    if request.method == "POST":
        try:
            service.update_checklist_item(item, **_recommendation_form())
        except (KeyError, ValueError) as exc:
            flash(str(exc), "error")
        else:
            flash("Rekomendacija atnaujinta", "success")
            return redirect(url_for("admin.recommendations"))

    return render_template(
        "admin/recommendation_form.html",
        item=item,
        platforms=QuestionRepository.get_all_platforms(),
        risk_areas=RISK_AREAS,
    )


@bp.route("/recommendations/<int:item_id>/delete", methods=["POST"])
@admin_required
def recommendation_delete(item_id: int):
    service = AdminService()
    item = service.get_checklist_item(item_id)
    if not item:
        abort(404)
    service.delete_checklist_item(item)
    flash("Rekomendacija ištrinta", "success")
    return redirect(url_for("admin.recommendations"))


@bp.route("/reports/sessions.csv")
@admin_required
def report_csv():
    return Response(
        AdminService().report_csv(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=secure-wizard-sesijos.csv"},
    )


def _required(field: str) -> str:
    value = request.form.get(field, "").strip()
    if not value:
        raise ValueError("Užpildykite visus privalomus laukus")
    return value


def _question_type() -> str:
    q_type = request.form.get("q_type", "")
    if q_type not in {"single", "multiple"}:
        raise ValueError("Neteisingas klausimo tipas")
    return q_type


def _risk_areas() -> list[str]:
    areas = [
        area.strip().upper()
        for area in request.form.getlist("risk_areas")
        if area.strip().upper() in RISK_AREAS
    ]
    if not areas:
        raise ValueError("Pasirinkite bent vieną rizikos sritį")
    return areas


def _risk_weight() -> int:
    value = int(request.form.get("risk_weight", "-1"))
    if not 0 <= value <= 10:
        raise ValueError("Rizikos svoris turi būti nuo 0 iki 10")
    return value


def _priority() -> int:
    value = int(request.form.get("priority", "0"))
    if not 1 <= value <= 5:
        raise ValueError("Prioritetas turi būti nuo 1 iki 5")
    return value


def _recommendation_form() -> dict:
    risk_area = request.form.get("risk_area", "").upper()
    if risk_area not in RISK_AREAS:
        raise ValueError("Pasirinkite rizikos sritį")
    return {
        "platform_code": request.form["platform"],
        "title": _required("title"),
        "description": _required("description"),
        "priority": _priority(),
        "risk_area": risk_area,
        "when_specialist": request.form.get("when_specialist", "").strip() or None,
    }
