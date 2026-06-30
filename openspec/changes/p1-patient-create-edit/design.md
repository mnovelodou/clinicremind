## Context

D1 created the `patients` table and the `Patient` SQLAlchemy model
(`app/models/patient.py`), which already stores phone as `country_code` +
`phone_national` and exposes a `phone_e164` property. What does not exist yet:
any HTML routes, any Jinja2 templates (there is no `app/templates/` directory),
and any phone-normalization logic — the model docstring explicitly defers
normalization to "P1/P2".

This is the project's first server-rendered UI, so P1 also stands up the
template baseline (a base layout, HTMX via CDN) that subsequent front-desk tasks
reuse. Auth does not exist yet, so the clinic is resolved from a hardcoded
single-clinic context per CLAUDE.md.

## Goals / Non-Goals

**Goals:**
- Normalize free-form phone input into `country_code` + `phone_national`,
  honoring the clinic's `default_country` when no `+` prefix is given.
- Create and edit a patient through validated HTML forms, scoped to the current
  clinic.
- Establish the Jinja2 + HTMX template baseline (base layout, form partial).

**Non-Goals:**
- Patient search (P2), detail/history (P3), find-next-appointment (P4).
- Patient deletion or merge.
- Role-based scoping / receptionist grants (arrives with Auth; P1 uses the
  hardcoded clinic).
- A reusable design system; styling stays minimal.

## Decisions

### In-house phone normalization (no `phonenumbers` library)
The schema stores digits-only `country_code` + `phone_national`, and the only
P1 requirement is "split input into those two parts, defaulting the country
code." A small helper — strip non-digits, detect a leading `+`/`00`, fall back
to the clinic's `default_country` dialing code — covers this without adding a
heavyweight dependency. Input is mapped from the clinic's ISO `default_country`
(e.g. `MX`) to its numeric dialing code (e.g. `52`) via a tiny lookup seeded
with the countries we actually serve.
- *Alternatives considered*: the `phonenumbers` (libphonenumber) package gives
  rigorous validation but is overkill for storing two digit strings and pulls in
  a large data table; we can adopt it later in P2 if real validation is needed.

### Hardcoded current-clinic helper
A single `current_clinic()` accessor returns the seeded clinic until Auth lands,
so routes filter every query by `clinic_id`. Centralizing it means the swap to a
real session-derived clinic in AU touches one function.

### Plain server-side validation (no WTForms yet)
Validation is simple: name required, email shape sanity-checked, phone
normalizable. A small validate-and-collect-errors function returning a dict of
field errors keeps the dependency footprint at zero and re-renders the form
fragment with errors inline (HTMX-friendly). WTForms can be introduced if forms
grow.

### Shared create/edit form template
Create and edit render the same form partial; the route supplies the action URL
and any pre-filled patient. HTMX posts the form and swaps in either a success
redirect (via `HX-Redirect`) or the re-rendered form with errors.

## Risks / Trade-offs

- **In-house normalization is naive** → it handles the digits-only storage
  contract but not edge cases (extensions, invalid lengths). Mitigation: keep
  the helper isolated and unit-tested so P2 can replace it with `phonenumbers`
  behind the same interface.
- **Hardcoded clinic context** → routes are unscoped by role and would leak
  across clinics if shipped as-is. Mitigation: this is explicitly the
  pre-Auth state mandated by CLAUDE.md; AU3 wraps these routes with scoping
  before multi-clinic/role use.
- **Country-code lookup table is partial** → an unmapped `default_country`
  can't resolve a dialing code. Mitigation: fall back gracefully (store national
  digits with a null country code rather than crashing) and cover the seeded
  clinic's country.
