# ClinicRemind — Implementation Plan

## Architecture Overview

- **Clinic** is the top-level entity. All data (patients, appointments, reminders) belongs to a clinic.
- **Users** are members of a clinic with a role (admin, receptionist, doctor). A solo dentist is just a clinic with one member.
- **Postgres is the source of truth** for everything — clinics, users, patients, appointments, reminders.
- **Google Calendar is a helper**, not a sync source. Appointments are added to Google Calendar via "Add to Google Calendar" links — no OAuth tokens stored. One-time import (OAuth, read events, discard tokens immediately) is available to help new clinics bootstrap data.
- **Background scheduler** (APScheduler) auto-sends WhatsApp reminders daily — no manual trigger needed.
- **Frontend** is server-rendered HTML (Jinja2 + HTMX + Alpine.js), served directly by Flask.

### Google Calendar role — links only, no stored tokens

```
User creates an appointment in ClinicRemind
  → Saved to Postgres (source of truth)
  → App generates an "Add to Google Calendar" link
  → Doctor/patient clicks the link → event added to their own Google Calendar
  → No OAuth, no API call, no tokens stored

One-time import (onboarding only):
  → User grants OAuth access (read-only, calendar.readonly scope)
  → App reads existing events, creates appointments + stub patients in Postgres
  → Tokens discarded immediately after import completes
  → After import, Postgres is the truth — no further connection to Google
```

"Add to Google Calendar" links are plain URLs of the form:
```
https://calendar.google.com/calendar/render?action=TEMPLATE
  &text=Appointment+at+Clínica+Rodríguez
  &dates=20250502T090000/20250502T100000
  &details=Notes+here
```
No auth required. Works for any Google account.

### Entity hierarchy

```
Clinic
  ├── Members (users with roles: admin | receptionist | doctor)
  ├── Patients (shared pool — belong to the clinic, not a specific doctor)
  └── Appointments (linked to a patient + optionally a doctor)
        └── "Add to Google Calendar" link (generated on the fly, no auth)
```

### Roles

| Role | Can do |
|---|---|
| **Admin / Owner** | Everything — settings, manage members, manage all appointments |
| **Receptionist** | Manage all appointments and patients, no settings |
| **Doctor** | View/manage their own appointments; optionally view others |

---

## Stack

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.12 | |
| Web framework | Flask | Simple, fast to build, serves pages + API routes |
| ORM | SQLAlchemy | Industry standard |
| Migrations | Alembic | Schema versioning |
| Database | PostgreSQL | Source of truth |
| Auth | Flask-Login + bcrypt | Session-based auth, no overengineering |
| Google Calendar (ongoing) | "Add to Google Calendar" links | No OAuth, no tokens, just a URL |
| Google Calendar (import) | google-auth-oauthlib + google-api-python-client | OAuth used once, tokens discarded after import |
| Scheduler | APScheduler | Runs inside Flask, cron-style jobs |
| Frontend | HTMX + Alpine.js + Jinja2 | Server-rendered, minimal JS, no build step |
| Hosting | TBD (Railway / Render / Fly.io) | |
| WhatsApp (v1) | `wa.me` links | Manual send, free |
| WhatsApp (v2) | Twilio API | Automatic send, upgrade path |

### Why HTMX + Alpine.js over a JS framework

Flask already serves HTML pages via Jinja2. HTMX lets you make those pages dynamic (partial updates, form submissions, modals) by returning HTML fragments from Flask routes — no JSON API layer, no frontend build step, no two codebases to maintain. Alpine.js handles small interactive bits (dropdowns, toggles). Fast to build, easy to debug.

### Google Calendar — no token storage needed

For day-to-day use, appointments are shared via a plain "Add to Google Calendar" URL — no OAuth, no API calls, no tokens.

For the one-time onboarding import:
```
User clicks "Import from Google Calendar"
  → OAuth consent screen (read-only scope: calendar.readonly)
  → App reads events, creates appointments + patients in Postgres
  → access_token and refresh_token discarded immediately
  → Import complete — no Google credentials stored anywhere
```

---

## Build Order

Build vertically — each milestone is a working slice from DB → backend → UI.
Riskiest and most valuable pieces first; auth wraps around what already works.

### M1 — Core data model
- [ ] Set up Flask project structure, SQLAlchemy, Alembic
- [ ] Define and migrate all tables (see schema below)
- [ ] Seed script with sample clinic, patients, appointments
- [ ] No auth yet — hardcode a single clinic context for development

### M2 — Appointments (the core of the product)
- [ ] Appointment list (day view, filterable by date and doctor)
- [ ] Create appointment (pick patient, doctor, date/time, notes)
- [ ] Edit / cancel appointment
- [ ] Status field: `pending | confirmed | cancelled`
- [ ] Patient picker with inline "create new patient" if not found

### M3 — Patient management
- [ ] Patient list (search by name or phone)
- [ ] Create / edit patient (name, phone, notes)
- [ ] Patient detail: appointment history

### M4 — Reminder engine
- [ ] Reminder message template per clinic (variables: `{name}`, `{date}`, `{time}`, `{notes}`)
- [ ] Clinic-level send time config (respects clinic timezone)
- [ ] APScheduler cron job: daily, per clinic, find next-day `pending` appointments → send reminders
- [ ] WhatsApp v1: generate `wa.me` pre-filled links, open in new tab (manual send)
- [ ] Track reminder state per appointment: `not_sent | sent | confirmed | cancelled`
- [ ] Guard: skip if appointment already confirmed or reminder sent recently
- [ ] Dashboard: tomorrow's appointments with reminder status at a glance
- [ ] Reminders screen: monitoring view — see what was sent, manually trigger if needed
- [ ] Follow-up screen: cancelled + no-reply list with direct WhatsApp links

### M5 — Auth & multi-user
- [ ] User signup → creates a clinic + adds them as admin
- [ ] User login (email + password)
- [ ] Session management (Flask-Login)
- [ ] All existing routes protected, scoped to the logged-in user's clinic
- [ ] Invite members by email (assign role on invite)
- [ ] Accept invite flow (register → land inside the clinic)
- [ ] Clinic settings page (name, phone, timezone, reminder schedule, template)
- [ ] User profile page (name, email, change password)

### M6 — Google Calendar integration
- [ ] Generate "Add to Google Calendar" link for every appointment (no auth required)
  - Link shown on appointment detail page and in reminder messages
- [ ] One-time import flow (onboarding):
  - [ ] OAuth consent (read-only scope: `calendar.readonly`)
  - [ ] Fetch events from selected calendar
  - [ ] Match events to existing patients by name/phone; create stubs for unmatched
  - [ ] Create appointments in Postgres
  - [ ] Discard tokens immediately after import — nothing stored
- [ ] Review queue: flag stub patients created during import for admin to complete

### M7 — Polish & edge cases
- [ ] Twilio integration for automatic WhatsApp sends (upgrade from `wa.me` links)
- [ ] Timezone handling per clinic
- [ ] Audit log: reminders sent, by whom, when
- [ ] Rate limiting on reminder sends
- [ ] Handle Google Calendar push failures gracefully (log, don't crash)
- [ ] Email fallback if WhatsApp not configured

---

## Database Schema

```
clinics
  id, name, phone, timezone, reminder_send_time, reminder_template, created_at

users
  id, email, password_hash, name, created_at

clinic_members
  id, clinic_id, user_id, role (admin | receptionist | doctor)

clinic_invites
  id, clinic_id, email, role, token, accepted_at, expires_at

patients
  id, clinic_id, name, phone, notes, is_stub, created_at, updated_at

appointments
  id, clinic_id, patient_id, doctor_user_id,
  start_at, end_at,
  status (pending | confirmed | cancelled),
  notes, created_at

reminders
  id, appointment_id, sent_at, status (not_sent | sent | confirmed | cancelled),
  method (wa_link | twilio), message_body
```

---

## Open Questions

1. Should a doctor be able to belong to more than one clinic? (e.g. works at two locations)
2. One-time Google Calendar import: auto-create stub patients, or hold in a review queue before creating appointments?
3. WhatsApp v1 (`wa.me` links) requires someone to manually tap "Send" on their phone — is that acceptable for the first version?
4. Should reminders be configurable per doctor (send time, template), or always clinic-wide?
5. Patient confirmation: is a WhatsApp reply the only channel, or do we also want a confirmation link (e.g. SMS / email)?
