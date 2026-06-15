"""Administratoriaus slaptažodžio maišos generavimas."""

import click
from werkzeug.security import generate_password_hash


@click.command("admin-hash")
@click.password_option(confirmation_prompt=True)
def admin_hash_command(password: str) -> None:
    """Sugeneruoja ADMIN_PASSWORD_HASH reikšmę."""
    click.echo(generate_password_hash(password))
