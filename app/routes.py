"""Application routes.

For F1 this is just a health/index endpoint that proves the app boots and can
reach the database. Domain routes arrive in later tasks.
"""

from __future__ import annotations

from flask import Blueprint, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .extensions import db

bp = Blueprint("main", __name__)


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
