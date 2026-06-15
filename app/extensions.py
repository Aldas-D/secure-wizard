"""Flask plėtinių inicializacija."""

from flask import request
from flask_limiter import Limiter
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect


def _client_ip() -> str:
    return request.remote_addr or "unknown"


db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
limiter = Limiter(key_func=_client_ip)
talisman = Talisman()
