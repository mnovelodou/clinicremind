## 1. Project tooling

- [x] 1.1 Add `requirements.txt` with pinned core deps (Flask, Flask-SQLAlchemy, SQLAlchemy, Alembic, psycopg, python-dotenv)
- [x] 1.2 Add `.env.example` documenting `DATABASE_URL` and `SECRET_KEY`
- [x] 1.3 Add/extend `.gitignore` for `.env`, `__pycache__`, virtualenv

## 2. Application factory & config

- [x] 2.1 Add `app/config.py` loading config from env, failing fast if `DATABASE_URL` is missing
- [x] 2.2 Add `app/extensions.py` defining the SQLAlchemy `db` instance
- [x] 2.3 Add `app/__init__.py` with `create_app(config_override=None)` wiring config, db, and routes
- [x] 2.4 Add `wsgi.py` entrypoint exposing the app

## 3. Health endpoint

- [x] 3.1 Add a health/index route that runs `SELECT 1` and returns 200 when DB is reachable
- [x] 3.2 Return a degraded/unhealthy response (not a bare 500) when the DB is unreachable

## 4. Migrations

- [x] 4.1 Initialize Alembic into `migrations/`
- [x] 4.2 Configure `env.py` to read `DATABASE_URL` from env and target `db.metadata`
- [x] 4.3 Generate the baseline (empty) migration revision

## 5. Verify

- [x] 5.1 Run `alembic upgrade head` against a local Postgres and confirm success
- [x] 5.2 Boot the app and confirm the health endpoint returns 200
- [x] 5.3 Add a minimal test that `create_app` builds with a test config and the health route responds
- [x] 5.4 Update README/CLAUDE setup notes with run instructions
