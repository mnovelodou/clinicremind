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

### Quick Postgres via Docker

```bash
docker run --name clinicremind-pg -e POSTGRES_USER=clinicremind \
  -e POSTGRES_PASSWORD=clinicremind -e POSTGRES_DB=clinicremind \
  -p 5432:5432 -d postgres:16
```

## Tests

```bash
pytest
```
