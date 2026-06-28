"""Alembic environment.

Reads the database URL from DATABASE_URL (the same variable the app uses) and
targets the application's SQLAlchemy metadata, so ``alembic revision
--autogenerate`` and ``alembic upgrade head`` stay in sync with the models that
later tasks define.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# Import the shared metadata. Importing the models package registers every
# table on db.metadata for autogenerate and upgrade.
import app.models  # noqa: F401  (import for side effect: registers tables)
from app.extensions import db

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

load_dotenv()
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError(
        "DATABASE_URL is required to run migrations. "
        "Copy .env.example to .env and set it."
    )
config.set_main_option("sqlalchemy.url", database_url)

target_metadata = db.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (emits SQL)."""
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
