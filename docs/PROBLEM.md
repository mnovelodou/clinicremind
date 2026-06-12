# ClinicRemind — Problem Statement

## The Problem

Clinics lose revenue every day from **no-shows** — patients who miss their appointment without notice. The root cause is almost always the same: the patient simply forgot.

Clinic staff know this, and they try to fix it manually by calling or messaging patients the day before. But this process is:

- **Inconsistent** — reminders depend on someone remembering to send them
- **Time-consuming** — staff have to go through the appointment list one by one
- **Untracked** — there is no record of who was reminded, who confirmed, and who went silent
- **Error-prone** — a busy day means reminders get skipped entirely

The result is a full schedule on paper that becomes a half-empty waiting room in practice.

---

## Who This Is For

Small-to-medium clinics (dental, medical, veterinary, physiotherapy, and similar) with:

- **One or more doctors** sharing a clinic (each with their own appointment schedule)
- **A receptionist or clinic staff member** who manages bookings and communications
- Patients contacted primarily via **WhatsApp**

---

## What We Are Building

ClinicRemind is an appointment scheduling, reminder, and confirmation tracking tool for clinics.

Staff schedule appointments directly in ClinicRemind — it is the single source of truth for the clinic's calendar. It then automatically sends WhatsApp reminders to patients the day before their appointment and tracks whether each patient confirmed, cancelled, or went silent — so staff can focus on what actually needs attention instead of manually chasing every patient.

### Core goals

1. **Eliminate missed reminders** — reminders go out automatically on a set schedule, no human trigger required
2. **Track confirmation status** — the clinic always knows who is confirmed, who is pending, and who cancelled
3. **Surface what needs action** — a clear follow-up view for cancellations and non-responders
4. **Support multiple doctors** — one clinic account handles all doctors and their schedules in a single view

### What it is not

- It is not a billing or payment system
- It is not a patient health records system

---

## The Outcome

A clinic using ClinicRemind should see:

- Fewer no-shows because patients are reliably reminded
- Less time spent by staff on manual follow-up calls and messages
- A clear daily view of who is coming, who confirmed, and who needs a follow-up
