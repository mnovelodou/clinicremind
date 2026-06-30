## ADDED Requirements

### Requirement: Seed CLI command

The system SHALL provide a `flask seed` command, registered on the application
factory's CLI, that populates a fixed sample dataset into the configured
database. The command SHALL run inside the Flask application context with the
SQLAlchemy session wired to the app's `DATABASE_URL`. The command SHALL NOT be
exposed as an HTTP route and SHALL NOT run automatically on application startup.

#### Scenario: Command is available on the app CLI

- **WHEN** `flask --app wsgi seed` is invoked against a migrated database
- **THEN** the command runs, writes the sample dataset, and exits with status 0

#### Scenario: Seeding requires the schema to exist

- **WHEN** `flask seed` is run against a database missing the D1 tables
- **THEN** the command fails with a clear error directing the operator to run
  migrations first, and writes no partial data

### Requirement: Fixed deterministic dataset

The seed dataset SHALL be a fixed, hardcoded set of rows (no random or
externally generated values) so that every run on an empty database produces the
same logical data. The dataset SHALL include exactly one clinic; at least three
doctors, of which at least one has a linked user and at least one has no linked
user; at least fifteen patients, each with a `country_code` and `phone_national`
populated; and at least thirty appointments distributed across past, present
(today), and future dates and covering every `appointment_status` enum value.

#### Scenario: Dataset is deterministic

- **WHEN** `flask seed` is run twice against two separate empty databases
- **THEN** both databases contain the same clinic, users, doctors, patients,
  and appointment rows (same natural-key values)

#### Scenario: Doctors include login-linked and login-less

- **WHEN** the seed completes
- **THEN** at least one seeded doctor has a non-null `user_id` and at least one
  seeded doctor has a null `user_id`

#### Scenario: Appointments span the lifecycle and the calendar

- **WHEN** the seed completes
- **THEN** seeded appointments include past, today, and future `start_at` values
  and include at least one appointment in each `appointment_status` state
  (`pending`, `confirmed`, `rescheduled`, `cancelled`, `no_show`)

#### Scenario: Patients carry two-part phone numbers

- **WHEN** the seed completes
- **THEN** every seeded patient has both `country_code` and `phone_national`
  populated with digits only, such that `phone_e164` reconstructs a valid number

### Requirement: Seeded logins with hashed passwords

The seed SHALL create `users` for an admin, a doctor, and a receptionist, each
with a bcrypt-hashed password and the corresponding `clinic_members` row(s)
using valid `member_role` enum values. The seed SHALL create at least one
`doctor_receptionist_grant` linking the receptionist user to a doctor. Plaintext
passwords MUST NOT be stored under any circumstances; only the bcrypt hash is
persisted.

#### Scenario: Passwords are stored hashed

- **WHEN** the seed completes
- **THEN** each seeded user's `password_hash` is a bcrypt hash that verifies
  against the documented dev password and is not the plaintext value

#### Scenario: Memberships use valid roles

- **WHEN** the seed completes
- **THEN** seeded `clinic_members` rows exist with roles `admin`,
  `receptionist`, and `doctor`, all within the `member_role` enum

#### Scenario: Receptionist grant created

- **WHEN** the seed completes
- **THEN** an active `doctor_receptionist_grant` (with `revoked_at` null) links
  the seeded receptionist user to a seeded doctor

### Requirement: Idempotent re-runs

Running the seed more than once SHALL NOT create duplicate rows or raise an
error. The command SHALL look up each entity by a stable natural key (clinic by
name, user by email, doctor by name, patient by name plus phone, appointment by
its doctor/patient/start_at) and create the row only when absent, leaving
existing rows in place.

#### Scenario: Second run is a no-op

- **WHEN** `flask seed` is run a second time against an already-seeded database
- **THEN** the command exits successfully and the row counts for every seeded
  table are unchanged from after the first run

#### Scenario: Partial dataset is completed

- **WHEN** `flask seed` is run against a database that contains some but not all
  seeded rows
- **THEN** the command inserts only the missing rows and leaves the existing
  ones untouched

### Requirement: Production safety guard

The seed command SHALL refuse to run whenever the application environment
indicates production. This guard is unconditional: there SHALL be no flag,
option, or environment override that re-enables seeding in production. The guard
SHALL be evaluated before any write occurs.

#### Scenario: Always blocked in production

- **WHEN** `flask seed` is invoked while the environment is `production`
- **THEN** the command aborts with a non-zero exit and writes no data,
  regardless of any flags or options supplied

#### Scenario: Allowed outside production

- **WHEN** `flask seed` is invoked while the environment is development or test
- **THEN** the command proceeds and seeds the dataset
