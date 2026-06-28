## Why

The D1 schema exists but the database is empty, so there is nothing to develop
or demo against. Task **S1** unblocks every downstream UI task (patients,
calendars, appointments) by giving developers a realistic, reproducible dataset
to build and click through without hand-entering rows or waiting on the auth and
CRUD flows that have not been built yet.

## What Changes

- Add a `flask seed` CLI command (registered on the app factory) that populates
  a fixed, deterministic sample dataset for local development and demos.
- Seed one clinic, ~3 doctors (a mix of login-linked and login-less), ~15
  patients with two-part phone numbers, and ~30 appointments spanning past,
  today, and future dates across the appointment-status lifecycle.
- Seed `users` (admin, doctor, receptionist) with **bcrypt-hashed** dev
  passwords, plus their `clinic_members` rows and one
  `doctor_receptionist_grant`, so logins work the moment AU1 lands.
- Make the command **idempotent**: it upserts by stable natural keys (clinic
  name, user email, patient name+phone) so re-running never duplicates or
  corrupts data.
- Add a **production guard**: the command aborts when the environment is
  `production` unless an explicit `--force` flag is passed. Seeding is CLI-only
  (no HTTP surface) and never wired into app startup.
- Add `bcrypt` to `requirements.txt` (needed here and by AU1).

## Capabilities

### New Capabilities
- `seed-data`: A developer/demo CLI command that idempotently installs a fixed,
  deterministic sample dataset for the iteration-1 schema, guarded against
  running in production.

### Modified Capabilities
<!-- None — no existing spec's requirements change. The data-model spec is
     consumed as-is; this change only reads/writes its tables. -->

## Impact

- New module(s) under `app/` for the seed dataset and CLI command
  (e.g. `app/seed.py`), registered via `app.cli` in the application factory.
- New dependency: `bcrypt` (pinned), also required by AU1.
- New helper for hashing passwords and (likely) a small phone-splitting helper
  used to populate `country_code` / `phone_national`.
- Writes to all eight D1 tables; no schema change, so **no Alembic migration**.
- README/CLAUDE setup notes gain a short "seed sample data" instruction.
- Tests covering idempotency (double-run is a no-op) and the production guard.
