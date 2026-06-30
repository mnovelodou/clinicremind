## 1. Dependencies & config

- [x] 1.1 Add `bcrypt` (pinned) to `requirements.txt` and install it
- [x] 1.2 Document `APP_ENV` in `.env.example` (e.g. `development`), noting that
      `production` unconditionally blocks `flask seed`

## 2. Helpers

- [x] 2.1 Add a `hash_password(plain) -> str` helper (wraps `bcrypt.hashpw`),
      reusable by AU1
- [x] 2.2 Add a small helper/structure to set patient `country_code` /
      `phone_national` from fixed digit strings

## 3. Seed dataset & command

- [x] 3.1 Create `app/seed.py` with the fixed dataset: 1 clinic; 3 doctors (≥1
      login-linked, ≥1 login-less); admin/doctor/receptionist users with hashed
      dev passwords; `clinic_members`; `clinic_doctors`; ≥15 patients; ≥1 active
      `doctor_receptionist_grant`; ≥30 appointments across past/today/future and
      all five `appointment_status` values
- [x] 3.2 Implement idempotent upsert: look up each entity by its natural key and
      insert only when absent; wrap the run in one transaction
- [x] 3.3 Implement the unconditional production guard: abort (non-zero, no
      writes) whenever `APP_ENV`/`FLASK_ENV` is `production` — no override flag
- [x] 3.4 Register the `seed` command (no options) on the app CLI in
      `create_app`

## 4. Tests

- [x] 4.1 Test that a run on an empty test DB creates the expected rows
      (counts, login-linked + login-less doctors, all statuses present, grant
      exists, passwords verify against the dev password and are not plaintext)
- [x] 4.2 Test idempotency: a second run leaves every seeded table's row count
      unchanged
- [x] 4.3 Test the production guard: blocked (non-zero, no writes) when
      `APP_ENV=production`, allowed in dev/test

## 5. Verify & document

- [x] 5.1 Run `flask --app wsgi seed` against a local migrated Postgres and
      confirm success; run it again and confirm it is a no-op
- [x] 5.2 Add a short "Seed sample data" section to README (and any needed note
      in CLAUDE.md) with the command and the dev login credentials
- [x] 5.3 Mark S1 `done` in `docs/BACKLOG.md` and link this change
