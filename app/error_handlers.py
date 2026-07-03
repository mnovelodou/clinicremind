"""App-wide error handlers.

The service layer raises domain exceptions; this is the one place that turns the
transport-agnostic ones (and uncaught failures) into HTTP responses, so no route
needs its own try/except for infrastructure errors. Route-specific domain
exceptions that map to normal control flow (``ValidationError`` re-rendering a
form, ``PatientNotFound`` → 404) are handled in the routes themselves.
"""

from __future__ import annotations

import logging

from flask import Flask, render_template
from werkzeug.exceptions import HTTPException

from app.services.exceptions import PersistenceError

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    """Attach the app-wide handlers to ``app``."""

    @app.errorhandler(PersistenceError)
    def _handle_persistence_error(exc: PersistenceError):
        logger.exception("Persistence error", exc_info=exc)
        return render_template("error.html", code=503, message="A database error occurred."), 503

    @app.errorhandler(HTTPException)
    def _handle_http_exception(exc: HTTPException):
        return (
            render_template("error.html", code=exc.code, message=exc.description),
            exc.code or 500,
        )

    @app.errorhandler(Exception)
    def _handle_unexpected(exc: Exception):
        logger.exception("Unhandled error", exc_info=exc)
        return render_template("error.html", code=500, message="Something went wrong."), 500
