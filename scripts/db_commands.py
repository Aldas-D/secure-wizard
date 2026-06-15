"""Duomenų bazės CLI komandos."""

import click
from flask.cli import with_appcontext

from app.extensions import db


@click.command("init-db")
@with_appcontext
def init_db_command() -> None:
    """Sukurti duomenų bazės lenteles."""
    db.create_all()
    click.echo("OK: DB lenteles sukurtos")


@click.command("drop-db")
@click.confirmation_option(prompt="Tikrai ištrinti visas lenteles?")
@with_appcontext
def drop_db_command() -> None:
    """Ištrinti duomenų bazės lenteles."""
    db.drop_all()
    click.echo("OK: DB lenteles istrintos")
