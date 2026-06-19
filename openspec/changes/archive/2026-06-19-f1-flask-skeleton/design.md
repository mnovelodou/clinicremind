## Context

ClinicRemind has no application code yet — only docs. F1 establishes the runnable
skeleton that D1 (tables/migrations) and everything after build into. The stack
is already decided in [CLAUDE.md](../../../CLAUDE.md): Python 3.12, Flask,
SGLAlchemy, SQLAlchemy, Alembic, Postgres, Flask-Login, Jinja2 + HTMX + Alpine. This change
must not introduce anything outside that stack and must leave clear conventions
for later tasks.

## Goals / Non-Goals

**Goals:**
- A Flask app that boots via an application factory and reads config from env.
- SQLAlchemy wired to Postgres with a clean per-request session lifecycle.
- Alembic configured to use the app's `DATABASE_URL` and metadata, with a
  baseline revision.
- A health endpoint that verifies DB connectivity.
- Reproducible setup (`requirements.txt`, `.env.example`, `.gitignore`).

**Non-Goals:**
- No domain tables/models (D1).
- No auth/login (AU track).
- No HTMX/Alpine front-end work beyond a trivial health/index page.
- No Docker/CI — local-run only for now.

## Decisions

- **Application-factory pattern (`create_app`)** over a module-level global app.
  Rationale: lets tests instantiate an app bound to a test database and avoids
  import-time side effects. Alternative (single global `app`) rejected — harder
  to test and scope.
- **Flask-SQLAlchemy** for session/engine management rather than hand-rolled
  SQLAlchemy `scoped_session`. Rationale: gives request-scoped sessions and
  teardown for free, is the conventional Flask choice, and integrates cleanly
  with Alembic via `db.metadata`. Alternative (raw SQLAlchemy) rejected as
  needless boilerplate for this stack.
- **psycopg (v3)** as the Postgres driver. Modern, maintained; SQLAlchemy 2.x
  supports it via the `postgresql+psycopg` URL scheme.
- **Alembic `env.py` reads `DATABASE_URL` from the environment** and targets
  `db.metadata`, so there is one source of truth for the connection string and
  autogenerate works once D1 defines models.
- **Layout**: `app/__init__.py` (factory), `app/extensions.py` (db instance),
  `app/config.py` (env-driven config), `app/routes.py` (health/index),
  `migrations/` (Alembic), `wsgi.py` (entrypoint). Keeps later blueprints easy
  to slot in.
- **Pin core dependencies** in `requirements.txt` for reproducible installs.

## Risks / Trade-offs

- [Health check that runs a DB query on every hit could add load] → keep it a
  cheap `SELECT 1`; it is a low-traffic internal endpoint.
- [Flask-SQLAlchemy couples us to its session model] → acceptable; it is part of
  the decided stack and the conventional choice.
- [Baseline empty migration may feel redundant] → it gives D1 a stable parent
  revision and keeps history linear.

## Migration Plan

1. Add dependencies and config files.
2. Add app factory, extensions, config, health route.
3. Initialize Alembic, point `env.py` at `DATABASE_URL` and `db.metadata`,
   generate the baseline revision.
4. Verify `alembic upgrade head` and the health endpoint locally.

Rollback: the change is additive (new files only); revert the branch.

## Open Questions

- None blocking. Connection-pool tuning and production WSGI server choice are
  deferred until deployment is in scope.
