# ClinicRemind

Appointment scheduling and follow-up tool for small/medium clinics. See
[CLAUDE.md](CLAUDE.md), [docs/PLAN.md](docs/PLAN.md), and
[docs/BACKLOG.md](docs/BACKLOG.md) for the problem, architecture, and task list.

## Stack

Python 3.12 · Flask · SQLAlchemy · Alembic · Postgres · Flask-Login + bcrypt ·
Jinja2 + HTMX + Alpine.js. No JS build step, no SPA, no JSON API.

## Local setup

Requires Python 3.12 and a Postgres database.

```bash
# 1. Create and activate a virtualenv
python3.12 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# edit .env: set DATABASE_URL and SECRET_KEY

# 4. Create the database (example with a local Postgres)
createdb clinicremind

# 5. Apply migrations
alembic upgrade head

# 6. Run the app
flask --app wsgi run --debug
```

Visit <http://localhost:5000/health> — it returns `200` with
`{"status": "ok", "database": "ok"}` when the app and database are healthy.

### Postgres via Docker Compose

```bash
docker compose up -d db
```

This starts Postgres and, on first boot, creates two databases:
`clinicremind` (development, matches `.env.example`) and `clinicremind_test`
(used by integration tests). Stop it with `docker compose down` (add `-v` to
also wipe the data volume).

## Tests

The suite has two layers:

* **Unit tests** — backed by in-memory SQLite, no external services.
* **Integration tests** (`@pytest.mark.integration`) — backed by a real
  Postgres, because they assert database-level guarantees (native enums,
  partial indexes, foreign keys) that SQLite does not enforce. They read
  `TEST_DATABASE_URL` and **skip** if no database is reachable.

```bash
pytest                          # everything (integration tests skip if no DB)
pytest -m "not integration"     # unit tests only — fast, no database
docker compose up -d db && pytest   # run the full suite, integration included
```
