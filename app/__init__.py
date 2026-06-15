"""Flask aplikacijos inicializavimas."""

import os
import secrets

from flask import Flask, g, jsonify, render_template, request
from pydantic import ValidationError
from sqlalchemy import event
from sqlalchemy.engine import Engine
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import ProductionConfig, get_config
from app.extensions import csrf, db, limiter, migrate, talisman
from app.logging_config import configure_logging, get_logger

logger = get_logger(__name__)


def create_app(config_name: str | None = None) -> Flask:
    configure_logging()

    app = Flask(__name__, instance_relative_config=True)
    config_cls = get_config(config_name)
    app.config.from_object(config_cls)

    if config_cls is ProductionConfig and (app.debug or app.testing):
        raise RuntimeError("DEBUG/TESTING režimas negali būti aktyvus produkcijoje")

    if config_cls is ProductionConfig:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    _init_extensions(app, config_cls)
    _configure_sqlite(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_cli_commands(app)
    _register_request_context(app)
    _register_security_headers(app)

    logger.info("app_initialized", env=config_name or os.environ.get("FLASK_ENV", "production"))
    return app


def _init_extensions(app: Flask, config_cls: type) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)

    if config_cls is ProductionConfig:
        talisman.init_app(
            app,
            force_https=True,
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,
            strict_transport_security_include_subdomains=True,
            session_cookie_secure=True,
            session_cookie_http_only=True,
            content_security_policy={
                "default-src": "'self'",
                "img-src": ["'self'", "data:"],
                "script-src": ["'self'"],
                "style-src": ["'self'", "'unsafe-inline'"],
                "style-src-elem": ["'self'", "'unsafe-inline'"],
                "font-src": ["'self'", "data:"],
                "connect-src": "'self'",
                "frame-ancestors": "'none'",
                "form-action": "'self'",
                "base-uri": "'self'",
                "object-src": "'none'",
            },
            content_security_policy_nonce_in=["script-src"],
            referrer_policy="strict-origin-when-cross-origin",
            permissions_policy={
                "geolocation": "()",
                "microphone": "()",
                "camera": "()",
                "payment": "()",
            },
        )


def _configure_sqlite(app: Flask) -> None:
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, _):  # noqa: ANN001
        if "sqlite" not in app.config["SQLALCHEMY_DATABASE_URI"]:
            return
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


def _register_blueprints(app: Flask) -> None:
    from app.blueprints.admin import bp as admin_bp
    from app.blueprints.api import bp as api_bp
    from app.blueprints.main import bp as main_bp
    from app.blueprints.quiz import bp as quiz_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(quiz_bp, url_prefix="/quiz")
    app.register_blueprint(api_bp, url_prefix="/api/v1")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    csrf.exempt(api_bp)


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ValidationError)
    def handle_validation(e: ValidationError):
        errors = e.errors(include_url=False, include_context=False)
        logger.warning("validation_error", errors=errors, request_id=getattr(g, "request_id", None))
        if request.is_json or request.path.startswith("/api/"):
            payload = {"error": "validation_error", "message": "Neteisingi įvesties duomenys"}
            return jsonify(payload), 422
        return render_template("errors/422.html"), 422

    @app.errorhandler(404)
    def not_found(_):
        if request.path.startswith("/api/"):
            return jsonify({"error": "not_found"}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(_):
        if request.path.startswith("/api/"):
            return jsonify({"error": "payload_too_large"}), 413
        return render_template("errors/422.html"), 413

    @app.errorhandler(429)
    def rate_limited(_):
        if request.path.startswith("/api/"):
            return jsonify({"error": "rate_limit_exceeded"}), 429
        return render_template("errors/422.html"), 429

    @app.errorhandler(500)
    def server_error(_):
        logger.exception("server_error", request_id=getattr(g, "request_id", None))
        if request.path.startswith("/api/"):
            return jsonify({"error": "internal_server_error"}), 500
        return render_template("errors/500.html"), 500


def _register_cli_commands(app: Flask) -> None:
    from scripts.admin_commands import admin_hash_command
    from scripts.db_commands import drop_db_command, init_db_command
    from scripts.seed_db import prepare_db_command, seed_command

    app.cli.add_command(seed_command)
    app.cli.add_command(init_db_command)
    app.cli.add_command(drop_db_command)
    app.cli.add_command(admin_hash_command)
    app.cli.add_command(prepare_db_command)


def _register_request_context(app: Flask) -> None:
    @app.before_request
    def attach_request_context():
        g.request_id = request.headers.get("X-Request-ID") or secrets.token_hex(8)
        if not hasattr(g, "csp_nonce"):
            g.csp_nonce = secrets.token_urlsafe(16)


def _register_security_headers(app: Flask) -> None:
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        if "X-Request-ID" not in response.headers and hasattr(g, "request_id"):
            response.headers["X-Request-ID"] = g.request_id
        return response
