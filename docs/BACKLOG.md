# ClinicRemind — Backlog

Machine-readable task list for autonomous pickup. See
[CLAUDE.md](../CLAUDE.md) for how to choose the next task. Dependency graph and
details live in [PLAN.md](PLAN.md).

**Statuses:** `todo` · `in_progress` · `blocked` · `done`
**Rule:** only start a `todo` task whose every dependency is `done`.

| ID | Task | Track | Depends on | Status | Spec |
|----|------|-------|-----------|--------|------|
| F1 | Flask + SQLAlchemy + Alembic skeleton | Foundation | — | done | [openspec](../openspec/changes/archive/2026-06-19-f1-flask-skeleton/) |
| D1 | Define & migrate all tables (clinics, users, clinic_members, doctors, doctor_receptionist_grants, patients, appointments) | Foundation | F1 | done | [openspec](../openspec/changes/archive/2026-06-28-d1-data-model/) |
| S1 | Seed script: sample clinic, doctors, patients, appointments | Foundation | D1 | done | [openspec](../openspec/changes/archive/2026-06-29-s1-seed-script/) |
| P1 | Patient model + create/edit | Patients | D1 | done | [openspec](../openspec/changes/p1-patient-create-edit/) |
| P2 | Patient search by name / phone (normalized) | Patients | P1 | todo | |
| P3 | Patient detail + appointment history | Patients | P1, A2 | todo | |
| P4 | Find next appointment(s) by patient (doctor-independent) | Patients | A2 | todo | |
| C1 | Doctor entity (optional user link) | Calendars | D1 | todo | |
| C2 | Per-doctor day/week calendar view | Calendars | C1, A2 | todo | |
| C3 | Combined all-doctors view + filter by doctor | Calendars | C2 | todo | |
| A1 | Create appointment (patient + doctor + time + notes, inline new patient) | Appointments | P1, C1 | todo | |
| A2 | Daily appointment list (date + doctor filter) | Appointments | A1 | todo | |
| A3 | Status lifecycle: confirm / cancel / reschedule / no-show | Appointments | A2 | todo | |
| I1 | Generate valid .ics from an appointment | ICS email | A1 | todo | |
| I2 | Email appointment with ICS attached (+ template) | ICS email | I1 | todo | |
| AU1 | Login, sessions (Flask-Login + bcrypt) | Auth | D1 | todo | |
| AU2 | Roles + multi-role users + route guards | Auth | AU1 | todo | |
| AU3 | Per-role data scoping (doctor/receptionist/admin/super admin) | Auth | AU2, A2, P2 | todo | |
| AU4 | Doctor→Receptionist grant management | Auth | AU3 | todo | |
| AU5 | Super Admin clinic-switching context | Auth | AU2 | todo | |
| R1 | Reminder engine (APScheduler, templates, state) | Iteration 2 | A3 | todo | |
| W1 | WhatsApp wa.me links → Twilio | Iteration 2 | A3, R1 | todo | |
| G1 | Google Calendar: add-to-calendar links | Iteration 2 | A1 | todo | |
| G2 | Google Calendar: availability / free-busy check on booking | Iteration 2 | C2, A1 | todo | |
| G3 | Google Calendar: one-time onboarding import | Iteration 2 | D1 | todo | |
| X1 | Dashboard: tomorrow's appointments + confirmation status | Iteration 2 | R1 | todo | |
| X2 | Follow-up view: cancellations + non-responders | Iteration 2 | R1 | todo | |
| L1 | Internationalization: English + Spanish UI strings (Flask-Babel, locale selection) | Platform | P1 | todo | |

## Notes
- IDs match the track letters in PLAN.md's dependency graph.
- When a task's dependency is itself `todo`/`in_progress`, leave the task as
  `todo` (it is implicitly blocked) — do not mark it `blocked` unless an external
  decision is needed.
