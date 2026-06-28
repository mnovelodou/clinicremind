## Context

D1 landed the full iteration-1 schema (eight tables, two enums) but the database
is empty. Auth (AU1) and the patient/appointment CRUD UIs do not exist yet, so
there is no in-app way to create data. Developers building P1/C1/A1 need a
realistic, repeatable dataset they can immediately read and render.

The app uses the application-factory pattern (`create_app` in
[app/__init__.py](app/__init__.py)), config is env-derived
([app/config.py](app/config.py)), and the SQLAlchemy `db` lives in
`app.extensions`. There is currently **no** `APP_ENV`/`FLASK_ENV` notion in
`Config`. The `users.password_hash` column is `String(255)`; a bcrypt hash is 60
chars, so it fits.

## Goals / Non-Goals

**Goals:**
- A `flask seed` CLI command that fills the D1 schema with a small, fixed,
  deterministic dataset for local dev and demos.
- Idempotent: re-running never duplicates rows or errors.
- Safe by default: cannot silently overwrite a production database.
- Seed real bcrypt-hashed logins so AU1 works against seeded users on day one.

**Non-Goals:**
- No schema change and no Alembic migration (seed only reads/writes existing
  tables).
- No Faker / random data, no configurable volume or CLI sizing flags beyond
  `--force`.
- No iteration-2 data (reminders, WhatsApp, Google Calendar).
- Not a production data-provisioning tool; it is a dev/demo fixture.

## Decisions

### Invocation: Flask CLI command on the app factory
Register the command via `app.cli.add_command(...)` (or `@app.cli.command`)
inside `create_app`, implemented in a new `app/seed.py`. Rationale: idiomatic
Flask, runs in app context with `db` already wired, no new HTTP surface, and
nothing runs at startup. Operators invoke `flask --app wsgi seed` from a trusted
shell.

### Dataset: fixed Python literals in `app/seed.py`
Define the clinic, users, doctors, clinic_doctors, patients, grants, and
appointments as hardcoded structures. Appointment `start_at` values are computed
relative to "today" (e.g. `today - 7d`, `today`, `today + 3d`) so the calendar
always has past/today/future rows, but the *set* of offsets is fixed — so it is
deterministic in shape while staying useful as the clock advances. All five
`appointment_status` values appear at least once.

### Idempotency: lookup-by-natural-key, then insert-if-absent
For each entity, query by a stable natural key before inserting:
- clinic → `name`
- user → `email`
- doctor → `name`
- clinic_doctor → `(clinic_id, doctor_id)`
- patient → `(clinic_id, name, phone_national)`
- grant → `(doctor_id, receptionist_user_id)` active
- appointment → `(doctor_id, patient_id, start_at)`

Existing rows are left untouched (no updates), so the command is a pure "fill
the gaps" operation. The whole run is wrapped in a single transaction that
commits at the end.

### Production guard: env check before any write
Read the environment from `APP_ENV` (falling back to `FLASK_ENV`), treating the
literal value `production` as protected; anything else (including unset) is
allowed. If protected and `--force` was not passed, abort with a non-zero exit
**before** opening the transaction. This keeps the guard independent of the
existing `Config` (which has no env-name field today) and avoids accidental
seeding of a prod database. Document `APP_ENV` in `.env.example`.

### Passwords: bcrypt via a small helper
Add `bcrypt` (pinned) to `requirements.txt`. A `hash_password(plain)` helper
wraps `bcrypt.hashpw`; the seed uses a single documented dev password
(`password`) for all seeded users. AU1 will reuse this helper for real
verification. The dev password is acceptable because the prod guard prevents
these accounts from being created anywhere real.

### Phone parts helper
Patients store `country_code` + `phone_national` separately. The seed sets both
fields directly from fixed digit strings (e.g. `"52"`, `"5512345678"`); a tiny
inline split is enough — no dependency on the P1/P2 normalization logic, which
does not exist yet.

## Risks / Trade-offs

- **Time-relative appointments aren't byte-identical across days.** Accepted:
  the spec's determinism requirement is about logical/natural-key identity and
  lifecycle coverage, not absolute timestamps. Relative dates keep the calendar
  demo meaningful over time, which matters more.
- **Env-name guard duplicates a concept `Config` lacks.** Reading `APP_ENV`
  directly is a small, self-contained check now; if `Config` later grows a
  first-class environment field, the guard can adopt it. Low cost to change.
- **Hardcoded dev password is weak by design.** Mitigated by the prod guard and
  by it being a fixture password only; never reused for real credentials.
- **Idempotency keys could collide** if two seeded patients shared name+phone.
  Avoided by construction — the fixed dataset uses distinct natural keys.
