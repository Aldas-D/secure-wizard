"""CSRF apsaugos integraciniai testai."""

import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def csrf_app():
    app = create_app("development")
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SERVER_NAME"] = "localhost"

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def csrf_client(csrf_app):
    return csrf_app.test_client()


def test_post_without_csrf_token_is_rejected(csrf_client):
    response = csrf_client.post("/quiz/start", data={"platform": "WIN"})
    assert response.status_code in (400, 403)


def test_api_endpoints_are_csrf_exempt(csrf_client):
    response = csrf_client.post(
        "/api/v1/sessions",
        json={"platform": "WIN"},
    )
    assert response.status_code != 403
