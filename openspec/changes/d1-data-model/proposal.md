## Why

The Flask + SQLAlchemy + Alembic skeleton (F1) is in place but the application
has no domain tables yet. Every iteration-1 feature (patients, doctors,
calendars, appointments, ICS email, auth/scoping) depends on a stable data
model. This change defines and migrates the complete iteration-1 schema so the
rest of the build order is unblocked.

## What Changes

- Add SQLAlchemy models for the eight core entities defined in
  [docs/PLAN.md](../../../docs/PLAN.md): `clinics`, `users`, `clinic_members`,
  `doctors`, `clinic_doctors`, `doctor_receptionist_grants`, `patients`,
  `appointments`.
- Encode the resolved decisions from PLAN.md as schema constraints:
  - Patients are clinic-wide contact records with **no clinical/medical data**.
  - Users ≠ doctors: a `doctor` may optionally link to a `user`; a user holds
    roles via `clinic_members` rows (a user can have multiple memberships).
  - Doctors are global identities that may work at multiple clinics, recorded in
    `clinic_doctors` (unique per clinic+doctor). Resolves Open Question #4.
  - Receptionist access is grant-based via `doctor_receptionist_grants`
    (nullable `revoked_at` = currently active grant).
  - Appointment status is an enum: `pending | confirmed | rescheduled |
    cancelled | no_show`.
- Store patient phone numbers as `country_code` + `phone_national` (both digits
  only); reconstruct the canonical E.164 number on demand rather than storing
  it. `phone_national` is the searchable column so the front desk can look up by
  local number without the country code. Numbers entered without a `+` default
  to the **clinic's** country (`clinics.default_country`). Resolves Open
  Question #1.
- Make patient `name` searchable by arbitrary substring via a `pg_trgm` GIN
  index (e.g. "novelo" matches "Jose Miguel Novelo Vargas").
- Add a single Alembic migration that installs `pg_trgm` and creates all tables,
  enum types, foreign keys, and indexes.
- The `reminders` table is **out of scope** (iteration 2).

## Capabilities

### New Capabilities
- `data-model`: The relational schema for ClinicRemind iteration 1 — clinics,
  users and memberships, doctors, receptionist grants, patients, and
  appointments — including keys, constraints, enums, and the Alembic migration
  that creates them.

### Modified Capabilities
<!-- None — app-foundation (F1) established the skeleton; this change adds new
     domain tables rather than altering existing requirements. -->

## Impact

- New SQLAlchemy model modules under `app/models/` (or equivalent existing
  layout established by F1).
- New Alembic migration under `migrations/versions/`.
- Postgres schema: 8 new tables + two enum types (appointment status, member
  role) + the `pg_trgm` extension; `clinics` gains a `default_country` column;
  `patients` carries `country_code` + `phone_national` and a trigram name index.
- Unblocks backlog tasks S1, P1, C1, A1, AU1 (everything depends on D1).
- No HTTP routes, templates, or auth behavior change in this task.
