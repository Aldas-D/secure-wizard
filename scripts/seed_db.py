"""DB užpildymas iš JSON failų. CLI komanda: flask seed."""

import json
from pathlib import Path

import click
from flask.cli import with_appcontext

from app.extensions import db
from app.logging_config import get_logger
from app.models import Answer, ChecklistItem, Platform, Question, Session, SessionAnswer

logger = get_logger(__name__)
DATA_DIR = Path(__file__).parent.parent / "app" / "data"


@click.command("seed")
@click.option("--reset", is_flag=True, help="Pirma ištrina visus duomenis")
@with_appcontext
def seed_command(reset: bool) -> None:
    """Užpildo DB klausimynais ir patikros veiksmais."""
    seed_data(reset)


@click.command("prepare-db")
@with_appcontext
def prepare_db_command() -> None:
    """Sukuria lenteles ir įkelia pradinius duomenis."""
    db.create_all()
    seed_data(False)


def seed_data(reset: bool) -> None:
    if reset:
        click.echo("Valomi esami duomenys...")
        SessionAnswer.query.delete()
        Session.query.delete()
        ChecklistItem.query.delete()
        Answer.query.delete()
        Question.query.delete()
        Platform.query.delete()
        db.session.commit()

    _seed_questions(DATA_DIR / "questions_windows.json")
    _seed_questions(DATA_DIR / "questions_android.json")
    _seed_checklist(DATA_DIR / "checklist_items.json")

    click.echo("OK: duomenys ikelti")


def _seed_questions(json_path: Path) -> None:
    if not json_path.exists():
        click.echo(f"Praleidziama: {json_path} nerastas")
        return

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    platform_data = data["platform"]
    platform = Platform.query.filter_by(code=platform_data["code"]).first()
    if not platform:
        platform = Platform(
            code=platform_data["code"],
            name=platform_data["name"],
            description=platform_data.get("description"),
        )
        db.session.add(platform)
        db.session.flush()
        click.echo(f"  + Platforma: {platform.code}")

    for q_data in data["questions"]:
        existing = Question.query.filter_by(
            platform_id=platform.id, order_num=q_data["order"]
        ).first()
        if existing:
            continue

        question = Question(
            platform_id=platform.id,
            text=q_data["text"],
            q_type=q_data["type"],
            order_num=q_data["order"],
        )
        question.risk_areas = q_data["risk_areas"]
        db.session.add(question)
        db.session.flush()

        for idx, a_data in enumerate(q_data["answers"]):
            answer = Answer(
                question_id=question.id,
                text=a_data["text"],
                risk_weight=a_data["weight"],
                order_num=idx,
            )
            db.session.add(answer)

    db.session.commit()
    click.echo(f"  + Klausimai: {platform.code}")


def _seed_checklist(json_path: Path) -> None:
    if not json_path.exists():
        click.echo(f"Praleidziama: {json_path} nerastas")
        return

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    for platform_code, items in data.items():
        platform = Platform.query.filter_by(code=platform_code).first()
        if not platform:
            continue

        for item_data in items:
            existing = ChecklistItem.query.filter_by(
                platform_id=platform.id, title=item_data["title"]
            ).first()
            if existing:
                continue

            item = ChecklistItem(
                platform_id=platform.id,
                title=item_data["title"],
                description=item_data["description"],
                priority=item_data["priority"],
                risk_area=item_data["risk_area"],
                when_specialist=item_data.get("when_specialist"),
            )
            item.trigger_answer_ids = item_data.get("trigger_answer_ids", [])
            db.session.add(item)

        click.echo(f"  + Patikros veiksmai: {platform_code}")

    db.session.commit()
