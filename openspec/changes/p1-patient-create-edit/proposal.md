## Why

The `patients` table exists (D1) but nothing in the application reads or writes
it. The front desk has no way to add a new contact record or correct an existing
one. P1 delivers the first patient-facing flow — create and edit — so later
tasks (search P2, detail/history P3, booking A1) have real records to work with.

## What Changes

- Add **phone-number normalization**: parse free-form phone input into the
  stored `country_code` + `phone_national` pair, defaulting the country code to
  the clinic's `default_country` when the user omits a leading `+`.
- Add a **create patient** flow: a form (name required; phone, email, notes
  optional), server-side validation, and persistence scoped to the current
  clinic.
- Add an **edit patient** flow: load an existing patient, pre-fill the form, and
  save changes (bumping `updated_at`).
- Add **Jinja2 + HTMX templates** and a base layout — the project's first
  server-rendered pages (none exist yet).
- Operate against the **hardcoded single-clinic context** until Auth (AU) lands;
  every patient query is filtered by that clinic id.

## Capabilities

### New Capabilities

- `patient-management`: creating and editing clinic-wide patient contact records,
  including phone-number normalization and form validation. (Search, detail, and
  history are added by later tasks under this same capability.)

### Modified Capabilities

<!-- None. The patients table/schema (data-model) is unchanged; this change only
     adds the application layer on top of it. -->

## Impact

- **New code**: a phone-normalization helper, patient create/edit routes (HTML),
  a patient form, and Jinja2 templates (base layout + form + list shell).
- **Touched**: `app/routes.py` / blueprint registration to mount the patient
  routes; `app/models/patient.py` may gain small helpers (e.g. apply-from-form).
- **Dependencies**: no new third-party libraries required (phone normalization
  is implemented in-house against `default_country`); HTMX is loaded via CDN in
  the base template — no JS build step.
- **No schema change**: no Alembic migration in this task.
- **Out of scope**: patient search (P2), detail + appointment history (P3),
  find-next-appointment (P4), patient deletion, and any role-based scoping
  (added with Auth).
