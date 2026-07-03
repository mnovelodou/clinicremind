# ClinicRemind — Application Architecture

This document defines how code inside `app/` is organized. The goal is
**separation of concerns**: business logic must not be tied to Flask, to HTMX,
or to SQLAlchemy, so we can grow use cases and later add delivery mechanisms (a
JSON API, a React/mobile client) or extract a service without rewriting the
core.

Read this before adding or moving code under `app/`. The layering rules here are
enforced conventions, not suggestions.

## Layers

Data flows **inward on the way down, DTOs on the way up**. The delivery layer
owns framework-specific input: a route reads `FormData`/`request` (a REST
endpoint would read a JSON body) and **translates it into a DTO** before calling
a service. Services only ever see DTOs — so the same service backs an HTMX form
today and a REST endpoint tomorrow with no change.

```
HTTP request  (FormData / JSON)
   │
   ▼
routes/        controllers — translate request → DTO, call a service, render/respond
   │  (DTOs in, DTOs out)         (FormData stops here)
   ▼
services/      business logic / use cases — validation, orchestration
   │  (models in from repos, DTOs out to routes)
   ▼
repositories/  the only place that runs SQLAlchemy queries
   │  (models in/out)
   ▼
models/        SQLAlchemy ORM models (the tables)

schemas/       DTOs — framework-free dataclasses that cross boundaries
mappers/       model ↔ DTO conversions (know both shapes)
utils/         stateless helpers (no HTTP, no DB) — e.g. phone normalization
context.py     request-scoped context (current clinic) — returns a DTO
```

### Directory map

| Directory / file      | Responsibility                                              | May import |
|-----------------------|-------------------------------------------------------------|------------|
| `routes/`             | HTTP: request→DTO, call service, build response/template    | services, schemas, context, extensions |
| `services/`           | Business logic / use cases; raises domain exceptions        | repositories, mappers, schemas, utils |
| `repositories/`       | SQLAlchemy queries for one aggregate                        | models, extensions |
| `models/`             | ORM models / table definitions                              | extensions |
| `schemas/`            | DTOs (`@dataclass`) — the boundary types                    | (nothing app-specific) |
| `mappers/`            | Convert models ↔ DTOs                                        | models, schemas, utils |
| `utils/`              | Stateless, domain-agnostic helpers                          | (nothing app-specific) |
| `context.py`          | Resolve the current clinic (pre-Auth: the seeded one)       | repositories, mappers, schemas |

## Rules

1. **Routes hold no business logic and issue no queries.** A route parses the
   request into a DTO, calls exactly one service, and turns the returned DTO (or
   a domain exception) into a response or template. Mapping a domain exception
   to an HTTP status (e.g. `PatientNotFound` → 404, `ValidationError` →
   re-rendered form) is controller work and belongs here.

2. **Services expose only DTOs.** A service may *receive* models from a
   repository and mutate them, but it must **never return a SQLAlchemy model**
   (or a live-session object) to a caller. Convert with a mapper first. Services
   raise domain exceptions (`app/services/exceptions.py`) — never `abort()`,
   never HTTP.

3. **Repositories are the only place with SQLAlchemy queries.** They accept and
   return models (models may be exposed *to services* here) and own the
   transaction boundary (`commit`). No `.query(...)` outside `repositories/`.

4. **Models never depend on services, routes, or schemas.** They know only the
   ORM (`app.extensions.db`).

5. **DTOs and utils are framework-free.** No Flask, no request, no session, no
   SQLAlchemy. This is what keeps the core reusable and unit-testable without a
   database or request context.

6. **One blueprint per module in `routes/`,** registered in the app factory
   (`app/__init__.py`).

7. **Naming.** DTO classes end in `DTO`; write-side input is `Create<X>DTO` /
   `Update<X>DTO`. Mapper functions are `to_<x>_dto` (model → DTO) and
   `to_model` / `apply_fields` (validated data → model). Repositories accept and
   return **models** (`create(patient)`), not loose kwargs.

8. **Error handling.** Repositories may raise `SQLAlchemyError`; services catch
   it and raise `PersistenceError` (a domain exception). App-wide handlers in
   `app/error_handlers.py` render domain/uncaught errors as HTTP responses, so
   routes only handle the domain exceptions that are normal control flow
   (`ValidationError`, `PatientNotFound`).

## Why this shape

- **Reuse across delivery mechanisms** — the same `PatientService` can back an
  HTMX form today and a JSON API or mobile backend tomorrow; only a new
  `routes/` module is added.
- **Extractable** — a repository + service pair has no Flask coupling, so moving
  a capability into its own service is a lift-and-shift, not a rewrite.
- **Testable** — pure validation/normalization (in `services`/`utils`) is unit
  tested with no database; repositories and routes get integration tests.

## Worked example: patient-management (P1)

| File                                    | Layer       |
|-----------------------------------------|-------------|
| `routes/patient_routes.py`              | controller  |
| `services/patient_service.py`           | use cases + validation |
| `services/exceptions.py`                | domain exceptions |
| `repositories/patient_repository.py`    | queries     |
| `models/patient.py`                     | ORM model   |
| `schemas/patient_dto.py`                | `CreatePatientDTO`/`UpdatePatientDTO` (in), `PatientDTO` (out) |
| `mappers/patient_mapper.py`             | model ↔ DTO |
| `utils/phone.py`                        | phone normalization |

A create request flows: `patient_routes.create` builds a `CreatePatientDTO` from
`request.form` and reads the clinic from `context.current_clinic()` →
`PatientService.create` validates (`build_patient_fields`), normalizes the phone
(`utils/phone`), builds a `Patient` model via `patient_mapper.to_model`, and asks
`PatientRepository.create(patient)` to persist → the returned model is mapped to
a `PatientDTO` via `to_patient_dto`. On bad input the service raises
`ValidationError` and the route re-renders the form fragment; on a DB failure it
raises `PersistenceError`, handled app-wide.
