"""ClinicRemind application package.

Exposes the ``create_app`` application factory. See ``app.config`` for
configuration and ``app.routes`` for the (currently minimal) routes.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from flask import Flask

from .config import Config
from .extensions import db


def create_app(config_override: Optional[Mapping[str, Any]] = None) -> Flask:
    """Build and return a configured Flask application.

    Args:
        config_override: Optional mapping applied on top of the env-derived
            config. Tests use this to point at a throwaway database.
    """
    app = Flask(__name__)

    config = Config.from_env()
    app.config.from_object(config)
    if config_override:
        app.config.update(config_override)

    db.init_app(app)

    # Import models so every table is registered on db.metadata.
    from . import models  # noqa: F401

    # One blueprint per delivery module (see app/routes/). Layering:
    # routes → services → repositories → models (docs/ARCHITECTURE.md).
    from .routes.health_routes import bp as health_bp
    from .routes.patient_routes import bp as patients_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(patients_bp)

    # CLI: `flask seed` populates deterministic sample data (dev/demo only).
    from .seed import seed_command

    app.cli.add_command(seed_command)

    return app
