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

**Patient phone — store the parts, reconstruct the whole.** Decision: `patients`
carries `country_code` (numeric dialing code, digits only, e.g. `52`) and
`phone_national` (national significant number, digits only, e.g. `5512345678`).
The canonical E.164 value is **not** a stored column — it is reconstructed when
needed as `"+" + country_code + phone_national` (a `Patient.phone_e164`
property). This avoids storing redundant, potentially-divergent data: the parts
are the source of truth. `phone_national` is the column indexed and matched for
search, so the front desk can find a patient by local number without typing a
country code.

**Country-code resolution defaults to the clinic.** A number entered with a
leading `+` is parsed as-is. A number entered without `+` is interpreted using
the clinic's default country: `clinics.default_country` (ISO 3166-1 alpha-2,
e.g. `MX`). So a bare `5512345678` typed at a Mexican clinic resolves to
country_code `52` + national `5512345678`. This is why D1 adds `default_country`
to `clinics`.

The parsing/normalization logic (likely the `phonenumbers` library) is
implemented in P1/P2; D1 only provides the columns
(`clinics.default_country`, `patients.country_code`, `patients.phone_national`)
and the index on `(clinic_id, phone_national)`.

**Name search by substring — trigram GIN index.** The front desk searches by any
fragment of a name (e.g. "novelo" must match "Jose Miguel Novelo Vargas"), which
a plain B-tree index cannot serve for infix `ILIKE '%…%'`. Decision: a
`pg_trgm` GIN index on `patients.name` (`gin_trgm_ops`) so substring search stays
index-backed; the clinic scope is applied as a separate `clinic_id = ?` filter.
The migration installs the `pg_trgm` extension (`CREATE EXTENSION IF NOT
EXISTS`). Alternative — a full-text `tsvector` — rejected because it tokenizes on
word boundaries and would miss partial-token matches like "nov".

**Grant lifecycle — soft state via `revoked_at NULL`.** An active grant has
`revoked_at IS NULL`; revoking sets the timestamp rather than deleting the row,
preserving history. A partial unique index on
`(doctor_id, receptionist_user_id) WHERE revoked_at IS NULL` prevents duplicate
active grants.

**Doctors are global identities; clinic membership is a join table.** A doctor
may work at several clinics (one at a time), so `doctors` does **not** carry a
`clinic_id`. Instead `clinic_doctors (clinic_id, doctor_id)` records which
clinics a doctor works at, with a unique constraint on the pair. Appointments and
grants still carry both `clinic_id` and `doctor_id` to pin the clinic context of
each row. This resolves PLAN.md Open Question #4. Alternative — duplicate the
doctor per clinic — rejected because it splits one person's identity and
calendar across rows.

**Indexes** — add indexes that the known iteration-1 queries need:
`appointments(clinic_id, doctor_id, start_at)` for calendar/day views,
`appointments(patient_id, start_at)` for patient history / next appointment,
`patients(clinic_id, phone_national)` and the `pg_trgm` GIN index on
`patients(name)` for search, plus FKs. Clinic-scoped tables carry `clinic_id`
with a FK to `clinics`.

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
- **Storing phone as parts, not E.164** → callers must reconstruct via the
  `phone_e164` property rather than reading a column. Mitigation: the property is
  the single reconstruction point; the parts can't drift out of sync.
- **`pg_trgm` is a Postgres extension** → the test schema (built from metadata,
  not the migration) must also install it. Mitigation: the integration fixture
  runs `CREATE EXTENSION IF NOT EXISTS pg_trgm` before `create_all`.
- **No DB-level guard against double-booking** (PLAN.md Open Question #2 is
  unresolved) → intentionally not enforced in D1; left to the A track. No schema
  constraint added so future policy stays open.

## Migration Plan

1. Add models under `app/models/`; import the package from `migrations/env.py`.
2. Create revision `0002_data_model` with `down_revision = "0001_baseline"`.
3. `upgrade()`: install `pg_trgm`, create tables (parents before children:
   clinics → users → clinic_members → doctors → patients → appointments →
   clinic_doctors → doctor_receptionist_grants) — enum types are auto-created by
   their first table — then indexes.
4. `downgrade()`: drop in reverse order, then drop the enum types (the `pg_trgm`
   extension is intentionally left installed).
5. Verify with `alembic upgrade head` then `alembic downgrade base` on a scratch
   DB to confirm both directions are clean.

## Open Questions

- None outstanding for D1. Multi-clinic doctors (former Open Question #4) are now
  modeled via `clinic_doctors`. Double-booking policy (Open Question #2) remains
  intentionally unconstrained at the schema level, deferred to the A track.
