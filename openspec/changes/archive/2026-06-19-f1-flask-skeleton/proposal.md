## Why

ClinicRemind has a problem statement, plan, and backlog but no runnable
application yet. Task **F1** is the foundation every other backlog item depends
on (D1 → S1 → all of Iteration 1). We need a minimal but conventional Flask +
SQLAlchemy + Alembic skeleton that boots, connects to Postgres, and runs
migrations — so subsequent tasks have a structure to build into.

## What Changes

- Introduce a Python 3.12 Flask application using the application-factory
  pattern (`create_app`).
- Add SQLAlchemy (configured against Postgres) and Alembic for migrations,
  wired so `alembic upgrade head` works against the app's database URL.
- Add configuration via environment variables (`.env` support), with a clear
  `DATABASE_URL` and `SECRET_KEY`.
- Add a health/index route proving the app boots and can reach the database.
- Add project tooling: `requirements.txt` (pinned core deps), `.env.example`,
  `.gitignore`, and a short run/setup section.
- No domain tables yet — those land in D1. This change ships an empty initial
  Alembic migration baseline so D1 can add the first real migration.

## Capabilities

### New Capabilities
- `app-foundation`: The runnable Flask application skeleton — app factory,
  configuration, database session wiring, migration tooling, and a health
  endpoint.

### Modified Capabilities
<!-- None — no existing specs yet. -->

## Impact

- New source tree (e.g. `app/`, `migrations/`, `wsgi.py` or `run.py`).
- New dependencies: Flask, SQLAlchemy, Alembic, psycopg, python-dotenv.
- Requires a local Postgres database to run.
- Establishes conventions (app factory, config, session lifecycle) that all
  later tasks inherit.
