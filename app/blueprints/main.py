"""Bendro pobūdžio puslapiai."""

from flask import Blueprint, jsonify, render_template

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/privatumas")
def privacy():
    return render_template("privacy.html")


@bp.route("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200
