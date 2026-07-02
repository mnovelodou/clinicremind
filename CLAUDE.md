# ClinicRemind — Agent Context

This file is the operating manual for any AI agent working in this repo. Read it
first, every session.

## What this project is

ClinicRemind is an appointment scheduling and follow-up tool for small/medium
clinics (dental, medical, veterinary, physio). The full problem statement is in
[docs/PROBLEM.md](docs/PROBLEM.md); the architecture, roles, schema, and task
dependency graph are in [docs/PLAN.md](docs/PLAN.md). **Read both before
starting work** — this file does not duplicate them.

One-line summary: clinics schedule appointments here (the source of truth),
look patients up by name/phone, manage the confirm/cancel/reschedule/no-show
lifecycle, and (iteration 1) email an `.ics` of the appointment. Iteration 2
adds WhatsApp follow-ups and Google Calendar.

## How to pick the next task

1. Open [docs/BACKLOG.md](docs/BACKLOG.md).
2. Pick the **highest task in the list whose status is `todo` and whose
   dependencies are all `done`**. Never start a task whose dependencies are
   unmet — the dependency graph in [docs/PLAN.md](docs/PLAN.md) is authoritative.
3. If several are unblocked, prefer the one earliest in the build order
   (Foundation → Patients/Calendars → Appointments → ICS/Auth → Iteration 2).
4. Set that task's status to `in_progress` in BACKLOG.md before writing code.

## Workflow for a task

1. **Write a spec first.** Create `docs/specs/<task-id>-<slug>.md` covering:
   data model touched, routes/pages, role/permission rules, acceptance
   criteria, and out-of-scope notes. Keep it short and concrete.
2. **Implement** against the spec, matching existing code conventions.
3. **Verify** (see Definition of Done).
4. Mark the task `done` in BACKLOG.md and link the spec.
5. Stop and summarize. Do **not** auto-start the next task unless explicitly
   asked to continue.

## Definition of Done

A task is done only when:
- The spec's acceptance criteria are met.
- Role/permission scoping is enforced (see role matrix in PLAN.md) — never ship
  a route that leaks another doctor's data.
- Alembic migration exists for any schema change.
- It runs locally without error and the happy path is manually verified.
- Tests exist for non-trivial logic (permission scoping, search, ICS generation).

## Conventions & guardrails

- **Stack is decided — do not swap it.** Python 3.12, Flask, SQLAlchemy,
  Alembic, Postgres, Flask-Login + bcrypt, Jinja2 + HTMX + Alpine.js. No JS
  build step, no SPA framework, no JSON API layer — return HTML fragments.
- **Postgres is the single source of truth.**
- **Patients are clinic-wide contact records — never store clinical/medical
  data.** A doctor's view of patients is *derived from their appointments*, not
  ownership.
- **Users ≠ doctors.** A user is a login; a doctor is a calendar owner that may
  or may not have a login. A user can be both admin and doctor.
- **Receptionist access is grant-based** (`doctor_receptionist_grants`). No
  grant = no visibility.
- **Iteration boundaries are firm.** Do not build WhatsApp, automated reminders,
  or Google Calendar until iteration 1 is complete. If a task seems to need
  them, re-read the scope — it probably doesn't.
- Early on, before Auth (AU) lands, features may run against a hardcoded
  single-clinic context. Once AU exists, every route must be scoped.

## Code architecture & layering

`app/` is **layered** — read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) before
adding or moving code there. Business logic must not be coupled to Flask, HTMX,
or SQLAlchemy, so use cases stay reusable (future JSON API / mobile) and
extractable. The flow is `routes → services → repositories → models`, with
`schemas/` (DTOs), `mappers/` (model ↔ DTO), and `utils/` (stateless helpers).

Non-negotiable rules:

- **Routes** (`routes/`, one blueprint per module) hold **no business logic and
  run no queries** — parse the request into a DTO, call one service, map the DTO
  result or a domain exception to a response/template.
- **Services** (`services/`) hold business logic and **expose only DTOs** — they
  may receive models from repositories but must never return a SQLAlchemy model.
  They raise domain exceptions (`services/exceptions.py`), never `abort()`/HTTP.
- **Repositories** (`repositories/`) are the **only** place with SQLAlchemy
  queries; they accept/return models and own the transaction boundary.
- **Models** (`models/`) depend only on the ORM. **DTOs** (`schemas/`) and
  **utils** (`utils/`) are framework-free (no Flask, no session).
- Don't add loose utility or route modules at the `app/` root — put them in the
  layer they belong to.

## When unsure

If a task is ambiguous or an open question in PLAN.md blocks it, write the
question into the spec under an "Open questions" heading and surface it rather
than guessing on something irreversible (schema shape, permission semantics).
