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

### Seed sample data

After migrations, load a fixed, deterministic sample dataset (one clinic, three
doctors, fifteen patients, thirty appointments across the status lifecycle, plus
admin/doctor/receptionist logins) for local development and demos:

```bash
flask --app wsgi seed
```

The command is **idempotent** — re-running it is a no-op, never a duplicate. It
**refuses to run in production** (when `APP_ENV` or `FLASK_ENV` is `production`),
with no override. Seeded logins all use the password `password`:

| Email                          | Role         |
|--------------------------------|--------------|
| `admin@clinicremind.test`      | admin        |
| `dr.reyes@clinicremind.test`   | doctor       |
| `reception@clinicremind.test`  | receptionist |

### Postgres via Docker Compose

```bash
docker compose up -d db
```

This starts Postgres and, on first boot, creates two databases:
`clinicremind` (development, matches `.env.example`) and `clinicremind_test`
(used by integration tests). Stop it with `docker compose down` (add `-v` to
also wipe the data volume).

## Tests

The suite is split into two trees that never mix:

* **`tests/unit/`** — pure unit tests. No database connection of any kind; the
  factory tests mock `db.init_app`. Fast, no external services.
* **`tests/integration/`** — backed by a real Postgres, because they assert
  database-level guarantees (native enums, partial indexes, foreign keys, a
  live `SELECT`) that SQLite or a mock cannot. They read `TEST_DATABASE_URL`
  and **skip** if no database is reachable. Everything here is auto-marked
  `integration`.

```bash
pytest tests/unit                   # unit only — fast, no database
docker compose up -d db && pytest   # full suite, integration included
pytest -m "not integration"         # unit only, by marker
```
