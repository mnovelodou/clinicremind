## 1. Phone normalization

- [ ] 1.1 Add a phone-normalization helper (e.g. `app/phone.py`) that strips
      non-digits, detects a `+`/`00` international prefix, and otherwise defaults
      the country code to the clinic's `default_country` dialing code; returns
      `(country_code, phone_national)` with `(None, None)` for blank input
- [ ] 1.2 Add an ISO-alpha-2 → numeric-dialing-code lookup covering the seeded
      clinic's country (e.g. `MX` → `52`), with graceful fallback when unmapped
- [ ] 1.3 Add a reverse helper to render stored `country_code` + `phone_national`
      back into a display value for pre-filling the edit form
- [ ] 1.4 Unit tests for normalization: local-number-defaults-to-clinic-country,
      international prefix retained, formatting stripped, blank → nulls

## 2. Clinic context & validation

- [ ] 2.1 Add a hardcoded `current_clinic()` helper resolving the seeded clinic
      (single point to swap for session-derived clinic when Auth lands)
- [ ] 2.2 Add patient input validation (name required, email shape sane, phone
      normalizable) returning a field→error map; unit-test the rules

## 3. Template baseline

- [ ] 3.1 Create `app/templates/` with a base layout that loads HTMX via CDN
      (no JS build step)
- [ ] 3.2 Create the shared patient form partial (name, phone, email, notes)
      that renders inline per-field errors and preserves submitted input

## 4. Create patient flow

- [ ] 4.1 Add GET route serving the create form and POST route that normalizes,
      validates, and inserts a patient scoped to `current_clinic()`
- [ ] 4.2 On success redirect (HTMX `HX-Redirect`); on failure re-render the
      form fragment with errors and preserved input
- [ ] 4.3 Register the patient blueprint/routes in the app factory

## 5. Edit patient flow

- [ ] 5.1 Add GET route loading a clinic-scoped patient (404 if outside the
      current clinic) and pre-filling the shared form
- [ ] 5.2 Add POST route that re-normalizes, re-validates, updates the row, and
      bumps `updated_at`

## 6. Verification

- [ ] 6.1 Route tests: create with valid input persists normalized phone;
      missing name re-renders with error; edit pre-fills and persists; edit of a
      patient outside the current clinic 404s
- [ ] 6.2 Run the app locally and manually verify the create and edit happy
      paths against the seeded clinic
- [ ] 6.3 Mark P1 `done` in `docs/BACKLOG.md` and link this change
