## Context

F1 established the Flask app factory, a shared `db = SQLAlchemy()` instance in
[app/extensions.py](../../../app/extensions.py), and an Alembic setup whose
`env.py` targets `db.metadata` with an empty `0001_baseline` revision as a
stable parent. No domain models exist yet. This change introduces the full
iteration-1 schema from [docs/PLAN.md](../../../docs/PLAN.md) as the next
Alembic revision on top of the baseline.

The schema and the decisions behind it are already resolved in PLAN.md; this
design records the concrete technical choices needed to translate that into
SQLAlchemy models and one migration.

## Goals / Non-Goals

**Goals:**
- SQLAlchemy models for the 7 core entities, registered on `db.metadata`.
- One Alembic migration (`0002_*`) on top of `0001_baseline` creating all
  tables, the appointment-status enum, foreign keys, and search/scoping indexes.
- Schema enforces the resolved decisions: clinic-wide patients with no clinical
  data, users-vs-doctors separation, grant-based receptionist access, four roles.
- `migrations/env.py` imports the models package so the metadata is populated.

**Non-Goals:**
- No CRUD routes, forms, templates, or business logic (those are P/C/A tasks).
- No auth/login wiring (AU tasks) — the `users` table exists but is not used for
  sessions here.
- No `reminders` table or any iteration-2 schema.
- No seed data (that is S1).

## Decisions

**Model layout — a `app/models/` package, one module per concern.**
F1 keeps modules flat under `app/` (`config.py`, `extensions.py`, `routes.py`).
Seven entities is enough to warrant a package: `app/models/__init__.py`
re-exports every model so `from app.models import *` / a single import in
`env.py` registers all tables on `db.metadata`. Alternative — one big
`models.py` — rejected as it will grow unwieldy as P/C/A add query helpers.

**Primary keys — `Integer` autoincrement.** Matches PLAN.md's `id` columns and
keeps URLs/seed scripts simple. UUIDs considered but unnecessary for a
single-database, server-rendered app.

**Appointment status — a Postgres `ENUM` type** (`appointment_status` with
`pending | confirmed | rescheduled | cancelled | no_show`), created explicitly
in the migration and referenced by the column. `rescheduled` marks an
appointment whose time was moved — the A3 lifecycle creates the replacement
appointment and stamps the original `rescheduled`, preserving the history rather
than mutating the original in place. Native enum gives DB-level validation. The
migration must `create_type`/`drop_type` the enum on up/down. Alternative — a
`VARCHAR` + CHECK constraint — rejected for weaker typing.

**Roles on `clinic_members.role`** — also a Postgres enum `member_role`
(`admin | receptionist | doctor`). `super_admin` is **not** a membership role;
it is the boolean `users.is_super_admin` (super admin operates above the clinic
boundary, per PLAN.md). A user may have multiple `clinic_members` rows.

**Patient phone — store E.164 canonical plus a searchable national number.**
Decision: `patients` carries two columns — `phone` (canonical **E.164**, with
country code, e.g. `+5215512345678`) and `phone_national` (the national
significant number, digits only, no country/trunk prefix, e.g. `5512345678`).
The front desk routinely searches by the local number without typing a country
code, so `phone_national` is the column indexed and matched for search; `phone`
is the canonical value used for display, ICS, and (iteration 2) WhatsApp.

**Country-code resolution defaults to the clinic.** A number entered with a
leading `+` is parsed as-is. A number entered without `+` is interpreted using
the clinic's default country: `clinics.default_country` (ISO 3166-1 alpha-2,
e.g. `MX`). So a bare `5512345678` typed at a Mexican clinic resolves to
`+525512345678`. This is why D1 adds `default_country` to `clinics`.

The parsing/normalization logic (likely the `phonenumbers` library) is
implemented in P1/P2; D1 only provides the three columns
(`clinics.default_country`, `patients.phone`, `patients.phone_national`) and the
index on `(clinic_id, phone_national)`. Storing both columns is a deliberate,
small denormalization to keep search fast and country-code-agnostic.

**Grant lifecycle — soft state via `revoked_at NULL`.** An active grant has
`revoked_at IS NULL`; revoking sets the timestamp rather than deleting the row,
preserving history. A partial unique index on
`(doctor_id, receptionist_user_id) WHERE revoked_at IS NULL` prevents duplicate
active grants.

**Indexes** — add indexes that the known iteration-1 queries need:
`appointments(clinic_id, doctor_id, start_at)` for calendar/day views,
`appointments(patient_id, start_at)` for patient history / next appointment,
`patients(clinic_id, phone_national)` and `patients(clinic_id, name)` for
search, plus FKs. Every clinic-scoped table carries `clinic_id` with a FK to `clinics`.

**Timestamps** — `created_at`/`updated_at` as timezone-aware `TIMESTAMP WITH
TIME ZONE`, server-default `now()`; `updated_at` maintained via SQLAlchemy
`onupdate`. `clinics.timezone` stored as text (IANA name) for later local-time
rendering.

## Risks / Trade-offs

- **Hand-written vs. autogenerated migration** → Autogenerate is convenient but
  can miss enum creation and partial indexes. Mitigation: generate as a
  starting point, then review/edit by hand to ensure enum types and the partial
  unique grant index are explicit and that `downgrade()` drops them cleanly.
- **Native Postgres enums are awkward to alter later** → adding a status value
  needs `ALTER TYPE`. Acceptable: the four appointment statuses and three roles
  are stable per PLAN.md's resolved decisions.
- **Committing to phone normalization now** → if normalization proves lossy for
  display, a later additive column is needed. Low risk, additive only.
- **No DB-level guard against double-booking** (PLAN.md Open Question #2 is
  unresolved) → intentionally not enforced in D1; left to the A track. No schema
  constraint added so future policy stays open.

## Migration Plan

1. Add models under `app/models/`; import the package from `migrations/env.py`.
2. Create revision `0002_data_model` with `down_revision = "0001_baseline"`.
3. `upgrade()`: create enum types, then tables (parents before children:
   clinics → users → clinic_members → doctors → patients →
   doctor_receptionist_grants → appointments), then indexes.
4. `downgrade()`: drop in reverse order, then drop the enum types.
5. Verify with `alembic upgrade head` then `alembic downgrade base` on a scratch
   DB to confirm both directions are clean.

## Open Questions

- PLAN.md Open Question #4 (a doctor belonging to multiple clinics) is left as
  designed: `doctors.clinic_id` is single-valued (one clinic per doctor row).
  Revisit only if multi-location support is prioritized; would be an additive
  change.
