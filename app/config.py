"""Application configuration, loaded from environment variables.

Configuration has a single source of truth: the process environment (optionally
populated from a local ``.env`` file). ``Config.from_env`` fails fast when a
required variable is missing so the app never boots in a half-configured state.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


class Config:
    """Resolved application configuration."""

    def __init__(self, database_url: str, secret_key: str, debug: bool = False) -> None:
        self.SQLALCHEMY_DATABASE_URI = database_url
        self.SECRET_KEY = secret_key
        self.DEBUG = debug
        # Surface connection issues fast and don't hand out stale connections.
        self.SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    @classmethod
    def from_env(cls) -> "Config":
        """Build configuration from environment variables.

        Loads ``.env`` if present (real env vars take precedence), then requires
        ``DATABASE_URL`` and ``SECRET_KEY``.
        """
        load_dotenv()

        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ConfigError(
                "DATABASE_URL is required. Copy .env.example to .env and set it."
            )

        secret_key = os.environ.get("SECRET_KEY")
        if not secret_key:
            raise ConfigError(
                "SECRET_KEY is required. Copy .env.example to .env and set it."
            )

        debug = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
        return cls(database_url=database_url, secret_key=secret_key, debug=debug)
