"""Shared extension instances.

Kept in their own module so both the app factory and Alembic's ``env.py`` can
import ``db`` (and therefore ``db.metadata``) without triggering a circular
import through the application package.
"""

from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy

# The single SQLAlchemy instance for the app. Flask-SQLAlchemy provides a
# request-scoped session that is torn down automatically at the end of each
# request, so no manual session lifecycle management is required.
db = SQLAlchemy()
