## ADDED Requirements

### Requirement: Clinic table

The system SHALL provide a `clinics` table as the top-level tenant entity. Each
clinic SHALL have an integer primary key, a name, an optional phone, an IANA
timezone string, a `default_country` (ISO 3166-1 alpha-2 code, e.g. `MX`) used
as the default country code when normalizing patient phone numbers, and a
creation timestamp.

#### Scenario: Clinic created with required fields

- **WHEN** a clinic row is inserted with a name, timezone, and default_country
- **THEN** it persists with an auto-assigned integer `id` and a `created_at`
  timestamp defaulted by the database

#### Scenario: Default country drives phone normalization

- **WHEN** a patient phone is entered without a leading `+` at a clinic whose
  `default_country` is `MX`
- **THEN** the number is normalized using the `+52` country code

#### Scenario: Clinic name is required

- **WHEN** a clinic row is inserted without a name
- **THEN** the database rejects the insert (NOT NULL violation)

### Requirement: User accounts

The system SHALL provide a `users` table representing logins. Each user SHALL
have an integer primary key, a unique email, a password hash, a name, a boolean
`is_super_admin` (default false), and a creation timestamp. A user is distinct
from a doctor.

#### Scenario: Email uniqueness enforced

- **WHEN** two users are inserted with the same email
- **THEN** the database rejects the second insert (unique violation)

#### Scenario: Super admin flag defaults to false

- **WHEN** a user is inserted without specifying `is_super_admin`
- **THEN** the stored value is false

### Requirement: Clinic memberships and roles

The system SHALL provide a `clinic_members` table linking a user to a clinic
with a role. The role SHALL be one of `admin`, `receptionist`, or `doctor`
(enforced by a database enum). A user MAY have more than one membership row in
the same clinic. `super_admin` SHALL NOT be a membership role; it is represented
by `users.is_super_admin`.

#### Scenario: Multiple roles for one user in a clinic

- **WHEN** a user has two membership rows in the same clinic with roles `admin`
  and `doctor`
- **THEN** both rows persist without conflict

#### Scenario: Invalid role rejected

- **WHEN** a membership row is inserted with role `super_admin` or any value
  outside the enum
- **THEN** the database rejects the insert

#### Scenario: Membership references valid clinic and user

- **WHEN** a membership row references a non-existent clinic or user
- **THEN** the database rejects the insert (foreign key violation)

### Requirement: Doctor calendar owners

The system SHALL provide a `doctors` table representing calendar owners as global
identities. A doctor SHALL have a name and creation timestamp, and MAY optionally
link to a user via a nullable `user_id`. A doctor without a linked user is valid.
A doctor SHALL NOT carry a `clinic_id`; the clinics a doctor works at are
recorded in `clinic_doctors` (see below).

#### Scenario: Doctor without a login

- **WHEN** a doctor row is inserted with `user_id` null
- **THEN** it persists as a calendar owner with no associated login

#### Scenario: Doctor linked to a user

- **WHEN** a doctor row is inserted with a `user_id` referencing an existing user
- **THEN** it persists and the link resolves to that user

### Requirement: Doctor–clinic membership

The system SHALL provide a `clinic_doctors` table recording which clinics a
doctor works at: integer primary key, `clinic_id`, `doctor_id`, and a creation
timestamp. A doctor MAY work at more than one clinic. At most one row SHALL exist
per `(clinic_id, doctor_id)` pair.

#### Scenario: Doctor works at multiple clinics

- **WHEN** a doctor is linked to two different clinics via `clinic_doctors`
- **THEN** both rows persist

#### Scenario: No duplicate clinic–doctor link

- **WHEN** a second `clinic_doctors` row is inserted for a `(clinic_id,
  doctor_id)` pair that already exists
- **THEN** the database rejects it (unique constraint violation)

### Requirement: Patient contact records

The system SHALL provide a `patients` table holding clinic-wide contact records:
integer primary key, `clinic_id`, name, a `country_code` (numeric dialing code,
digits only), a `phone_national` (national significant number, digits only),
email, free-text notes, and `created_at`/`updated_at` timestamps. The canonical
E.164 number SHALL NOT be stored as a column; it is reconstructed from
`country_code` + `phone_national`. Patients SHALL NOT include any clinical or
medical fields. The `phone_national` column SHALL be indexed together with
`clinic_id`. `name` SHALL be searchable by arbitrary substring, backed by a
trigram (`pg_trgm`) GIN index.

#### Scenario: Patient is clinic-scoped

- **WHEN** a patient row is inserted with a `clinic_id`
- **THEN** it persists scoped to that clinic and is not duplicated per doctor

#### Scenario: No clinical data stored

- **WHEN** the patients schema is inspected
- **THEN** it contains only contact fields (name, country_code, phone_national,
  email, notes) and no clinical/medical columns

#### Scenario: Searchable by national number without country code

- **WHEN** the patients table is created
- **THEN** an index exists on `(clinic_id, phone_national)`, allowing a patient
  to be found by their local number without typing the country code

#### Scenario: Searchable by partial name

- **WHEN** a patient named "Jose Miguel Novelo Vargas" exists and the front desk
  searches for the fragment "novelo"
- **THEN** the patient is found (case-insensitive substring match, backed by the
  trigram GIN index)

#### Scenario: Canonical phone reconstructed from parts

- **WHEN** a patient is saved with `country_code` `52` and `phone_national`
  `5512345678`
- **THEN** the canonical E.164 number is reconstructed as `+525512345678`

### Requirement: Receptionist access grants

The system SHALL provide a `doctor_receptionist_grants` table recording which
receptionist user may act for which doctor. Each grant SHALL have `clinic_id`,
`doctor_id`, `receptionist_user_id`, a `granted_at` timestamp, and a nullable
`revoked_at`. A grant with `revoked_at IS NULL` is active. At most one active
grant SHALL exist for a given `(doctor_id, receptionist_user_id)` pair.

#### Scenario: Active grant created

- **WHEN** a grant is inserted with `revoked_at` null
- **THEN** it represents an active grant of that doctor's data to the
  receptionist

#### Scenario: Revocation preserves history

- **WHEN** an active grant is revoked by setting `revoked_at`
- **THEN** the row remains and is no longer active

#### Scenario: No duplicate active grants

- **WHEN** a second active grant is inserted for a `(doctor_id,
  receptionist_user_id)` pair that already has an active grant
- **THEN** the database rejects it (partial unique index violation)

### Requirement: Appointments

The system SHALL provide an `appointments` table linking a patient and a doctor
within a clinic. Each appointment SHALL have `clinic_id`, `patient_id`,
`doctor_id`, `start_at`, `end_at`, a `status`, free-text notes, and
`created_at`/`updated_at` timestamps. `status` SHALL be a database enum with
values `pending`, `confirmed`, `rescheduled`, `cancelled`, `no_show`, defaulting
to `pending`. `rescheduled` marks an appointment whose time was moved to a
replacement appointment.
Indexes SHALL support calendar views (`clinic_id, doctor_id, start_at`) and
patient history (`patient_id, start_at`).

#### Scenario: Appointment defaults to pending

- **WHEN** an appointment is inserted without specifying status
- **THEN** the stored status is `pending`

#### Scenario: Invalid status rejected

- **WHEN** an appointment is inserted with a status outside the enum
- **THEN** the database rejects the insert

#### Scenario: Appointment references valid patient and doctor

- **WHEN** an appointment references a non-existent patient or doctor
- **THEN** the database rejects the insert (foreign key violation)

#### Scenario: Calendar and history indexes exist

- **WHEN** the appointments table is created
- **THEN** indexes exist on `(clinic_id, doctor_id, start_at)` and
  `(patient_id, start_at)`

### Requirement: Alembic migration for the data model

The system SHALL include a single Alembic migration, with `down_revision` set to
`0001_baseline`, that installs the `pg_trgm` extension and creates all eight
tables, the `appointment_status` and `member_role` enum types, foreign keys, and
the required indexes. The migration SHALL apply and roll back cleanly. The
`migrations/env.py` SHALL import the models so `db.metadata` is fully populated.

#### Scenario: Upgrade creates the full schema

- **WHEN** `alembic upgrade head` runs against an empty database at the baseline
  revision
- **THEN** the `pg_trgm` extension, all eight tables, both enum types, and all
  indexes are created without error

#### Scenario: Downgrade reverses cleanly

- **WHEN** `alembic downgrade base` runs after the upgrade
- **THEN** all tables, indexes, and enum types created by this migration are
  dropped without error

#### Scenario: Iteration-2 tables excluded

- **WHEN** the migration is applied
- **THEN** no `reminders` table (or other iteration-2 schema) is created
