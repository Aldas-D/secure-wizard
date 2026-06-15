"""Bendro pobūdžio puslapiai."""

from flask import Blueprint, jsonify, render_template

from app.extensions import talisman

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/privatumas")
def privacy():
    return render_template("privacy.html")


@bp.route("/healthz")
@talisman(force_https=False, content_security_policy=None)
def healthz():
    return jsonify({"status": "ok"}), 200
