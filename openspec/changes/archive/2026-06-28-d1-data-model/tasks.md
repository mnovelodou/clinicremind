## 1. Models package scaffolding

- [x] 1.1 Create `app/models/` package with `__init__.py` that re-exports every
  model so importing the package registers all tables on `db.metadata`
- [x] 1.2 Update `migrations/env.py` to `import app.models` so autogenerate and
  metadata are fully populated

## 2. Reference data models (clinics, users)

- [x] 2.1 Add `Clinic` model (`clinics`): id, name (not null), phone (nullable),
  timezone (IANA text), default_country (ISO 3166-1 alpha-2, e.g. `MX`),
  created_at (tz-aware, server default now())
- [x] 2.2 Add `User` model (`users`): id, email (unique, not null),
  password_hash, name, is_super_admin (bool, default false), created_at

## 3. Membership, doctors, grants

- [x] 3.1 Define `member_role` enum (`admin | receptionist | doctor`) and
  `ClinicMember` model (`clinic_members`): id, clinic_id FK, user_id FK, role;
  allow multiple rows per (user, clinic)
- [x] 3.2 Add `Doctor` model (`doctors`): id, user_id FK (nullable), name,
  created_at — a global identity, no clinic_id
- [x] 3.3 Add `ClinicDoctor` model (`clinic_doctors`): id, clinic_id FK,
  doctor_id FK, created_at; unique on `(clinic_id, doctor_id)` — a doctor may
  work at multiple clinics
- [x] 3.4 Add `DoctorReceptionistGrant` model
  (`doctor_receptionist_grants`): id, clinic_id FK, doctor_id FK,
  receptionist_user_id FK, granted_at, revoked_at (nullable); add a partial
  unique index on `(doctor_id, receptionist_user_id) WHERE revoked_at IS NULL`

## 4. Patients & appointments

- [x] 4.1 Add `Patient` model (`patients`): id, clinic_id FK, name,
  country_code (digits), phone_national (digits), email, notes, created_at,
  updated_at (onupdate); no clinical fields; `phone_e164` property reconstructs
  the canonical number; index `(clinic_id, phone_national)` and a pg_trgm GIN
  index on `name` for substring search
- [x] 4.2 Define `appointment_status` enum (`pending | confirmed | rescheduled |
  cancelled | no_show`) and `Appointment` model (`appointments`): id, clinic_id FK,
  patient_id FK, doctor_id FK, start_at, end_at, status (default pending),
  notes, created_at, updated_at; indexes on `(clinic_id, doctor_id, start_at)`
  and `(patient_id, start_at)`

## 5. Migration

- [x] 5.1 Generate the migration with autogenerate, set
  `down_revision = "0001_baseline"`, then hand-edit so `pg_trgm` is installed,
  enum types are dropped on downgrade, and the partial unique grant index is
  explicit
- [x] 5.2 Ensure `upgrade()` creates parents before children and `downgrade()`
  drops in reverse order and removes both enum types

## 6. Verification

- [x] 6.1 Run `alembic upgrade head` on a scratch DB; confirm all 8 tables, both
  enums, the pg_trgm extension, and all indexes exist (no `reminders` table)
- [x] 6.2 Run `alembic downgrade base`; confirm tables, indexes, and enum types
  are all dropped cleanly
- [x] 6.3 Add tests for non-trivial schema invariants: enum rejection
  (invalid role / status), unique email, no-duplicate-active-grant partial
  index, FK enforcement, partial-name search, phone reconstruction, and
  multi-clinic doctors
- [x] 6.4 Mark D1 `done` in `docs/BACKLOG.md` and link this OpenSpec change
