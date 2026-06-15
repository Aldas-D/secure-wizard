"""Bendri pytest fixtures visiems testams."""

import pytest

from app import create_app
from app.extensions import db as _db
from app.models import Answer, ChecklistItem, Platform, Question


@pytest.fixture(scope="session")
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    _db.create_all()
    yield _db
    _db.session.rollback()
    for table in reversed(_db.metadata.sorted_tables):
        _db.session.execute(table.delete())
    _db.session.commit()
    _db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def platform_win(db):
    platform = Platform(code="WIN", name="Windows", description="Test Windows")
    db.session.add(platform)
    db.session.flush()

    q1 = Question(
        platform_id=platform.id,
        text="Test klausimas 1",
        q_type="single",
        order_num=1,
    )
    q1.risk_areas = ["PWD"]
    db.session.add(q1)
    db.session.flush()

    db.session.add_all(
        [
            Answer(question_id=q1.id, text="Saugu", risk_weight=0, order_num=0),
            Answer(question_id=q1.id, text="Vidutiniškai", risk_weight=5, order_num=1),
            Answer(question_id=q1.id, text="Nesaugu", risk_weight=10, order_num=2),
        ]
    )

    q2 = Question(
        platform_id=platform.id,
        text="Test klausimas 2",
        q_type="single",
        order_num=2,
    )
    q2.risk_areas = ["NET"]
    db.session.add(q2)
    db.session.flush()

    db.session.add_all(
        [
            Answer(question_id=q2.id, text="Saugu", risk_weight=0, order_num=0),
            Answer(question_id=q2.id, text="Nesaugu", risk_weight=9, order_num=1),
        ]
    )

    item = ChecklistItem(
        platform_id=platform.id,
        title="Pakeisti slaptažodį",
        description="Test aprašymas",
        priority=1,
        risk_area="PWD",
    )
    item.trigger_answer_ids = []
    db.session.add(item)

    db.session.commit()
    return platform
