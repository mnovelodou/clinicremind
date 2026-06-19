# ClinicRemind — Project Context

Appointment scheduling and follow-up tool for small/medium clinics. Postgres is
the single source of truth. See [CLAUDE.md](../CLAUDE.md), [docs/PLAN.md](../docs/PLAN.md),
and [docs/BACKLOG.md](../docs/BACKLOG.md) for full detail.

## Stack (decided — do not swap)

- Python 3.12, Flask, SQLAlchemy, Alembic, Postgres
- Flask-Login + bcrypt for auth
- Jinja2 + HTMX + Alpine.js — no JS build step, no SPA, no JSON API (return HTML fragments)

## Conventions

- Postgres is the single source of truth.
- Patients are clinic-wide contact records — never store clinical/medical data.
- Users ≠ doctors. A user is a login; a doctor is a calendar owner.
- Receptionist access is grant-based.
- Iteration boundaries are firm (no WhatsApp / reminders / Google Calendar until iteration 1 done).
