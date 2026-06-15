"""Administravimo srities integraciniai testai."""
from werkzeug.security import generate_password_hash

from app.extensions import db as database
from app.models import Question, Session


def _login(client, app):
    app.config["ADMIN_USERNAME"] = "admin"
    app.config["ADMIN_PASSWORD_HASH"] = generate_password_hash("Test-password-123")
    return client.post(
        "/admin/login",
        data={"username": "admin", "password": "Test-password-123"},
    )


def test_admin_requires_login(client):
    response = client.get("/admin/")
    assert response.status_code == 302
    assert "/admin/login" in response.headers["Location"]


def test_admin_login_and_report(client, app, platform_win):
    response = _login(client, app)
    assert response.status_code == 302

    response = client.get("/admin/")
    assert response.status_code == 200
    assert b"Sistemos skydelis" in response.data

    response = client.get("/admin/reports/sessions.csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"


def test_admin_dashboard_counts_completed_sessions(client, app, platform_win):
    database.session.add_all(
        [
            Session(token_hash="a" * 64, platform_id=platform_win.id, completed=True),
            Session(token_hash="b" * 64, platform_id=platform_win.id, completed=False),
        ]
    )
    database.session.commit()
    _login(client, app)

    response = client.get("/admin/")

    assert response.status_code == 200
    assert b"50%" in response.data


def test_invalid_admin_hash_does_not_crash(client, app):
    app.config["ADMIN_PASSWORD_HASH"] = "1"
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "admin"},
    )
    assert response.status_code == 200
    assert b"Neteisingas" in response.data


def test_admin_question_crud(client, app, db, platform_win):
    _login(client, app)

    response = client.post(
        "/admin/questions/new",
        data={
            "platform": "WIN",
            "text": "Ar naudojate ekrano užraktą?",
            "q_type": "single",
            "risk_areas": ["ACC"],
        },
    )
    assert response.status_code == 302

    question = Question.query.filter_by(text="Ar naudojate ekrano užraktą?").one()
    response = client.post(
        f"/admin/questions/{question.id}/answers",
        data={"answer_text": "Taip", "risk_weight": "0"},
    )
    assert response.status_code == 302
    assert len(question.answers) == 1

    response = client.post(f"/admin/questions/{question.id}/delete")
    assert response.status_code == 302
    assert db.session.get(Question, question.id) is None
