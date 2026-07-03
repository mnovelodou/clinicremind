"""Health / index endpoint (app-foundation capability).

Proves the app boots and can reach the database. Domain routes live in their own
blueprints (e.g. ``patient_routes``).
"""

from __future__ import annotations

from flask import Blueprint, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db

bp = Blueprint("health", __name__)


@bp.route("/")
@bp.route("/health")
def health():
    """Report whether the app is up and the database is reachable.

    Returns 200 when a trivial ``SELECT 1`` succeeds, and 503 (not a bare 500)
    with context when the database cannot be reached.
    """
    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        return (
            jsonify(status="degraded", app="ok", database="unreachable", error=str(exc)),
            503,
        )

    return jsonify(status="ok", app="ok", database="ok"), 200
