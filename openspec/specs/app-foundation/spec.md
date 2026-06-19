# app-foundation

## Purpose

The runnable Flask application skeleton — application factory, environment-driven
configuration, database session wiring, migration tooling, and a health
endpoint. This is the foundation every other capability builds on.

## Requirements

### Requirement: Application factory

The system SHALL expose a `create_app()` application factory that builds and
returns a configured Flask application. Configuration MUST be loadable from
environment variables (with `.env` support), and the factory MUST accept a
config override so tests can run against a separate database.

#### Scenario: App boots from the factory

- **WHEN** `create_app()` is called with valid configuration
- **THEN** it returns a Flask app instance with `SECRET_KEY` and the SQLAlchemy
  database engine configured from `DATABASE_URL`

#### Scenario: Missing required configuration fails fast

- **WHEN** `create_app()` is called without a `DATABASE_URL`
- **THEN** the application raises a clear configuration error rather than
  starting in a broken state

### Requirement: Database session wiring

The system SHALL configure SQLAlchemy against Postgres and provide a request-
scoped session that is created per request and closed/removed when the request
ends, with no leaked connections.

#### Scenario: Session available during a request

- **WHEN** a request handler runs
- **THEN** a working SQLAlchemy session is available and committed/rolled back
  and removed at the end of the request

### Requirement: Migration tooling

The system SHALL include Alembic configured to read the application's
`DATABASE_URL` and target the SQLAlchemy metadata, so that `alembic upgrade
head` applies migrations against the configured database.

#### Scenario: Migrations run against the configured database

- **WHEN** `alembic upgrade head` is run with a valid `DATABASE_URL`
- **THEN** Alembic connects to that database and applies all migrations to the
  latest revision without error

#### Scenario: Baseline migration exists

- **WHEN** the repository is first set up
- **THEN** an initial Alembic baseline revision exists so later tasks add domain
  tables as new revisions on top of it

### Requirement: Health endpoint

The system SHALL expose a health/index route that confirms the app is running
and can reach the database.

#### Scenario: Health check succeeds

- **WHEN** a client requests the health route and the database is reachable
- **THEN** the response status is 200 and indicates the app and database are
  healthy

#### Scenario: Health check reports database failure

- **WHEN** the database is unreachable and the health route is requested
- **THEN** the response indicates an unhealthy/degraded state rather than a
  generic 500 with no context

### Requirement: Project setup tooling

The system SHALL provide pinned core dependencies and the files needed to set up
and run the app locally without guesswork.

#### Scenario: Dependencies are reproducible

- **WHEN** a developer installs from `requirements.txt`
- **THEN** Flask, SQLAlchemy, Alembic, the Postgres driver, and dotenv support
  are installed at pinned versions

#### Scenario: Environment is documented

- **WHEN** a developer copies `.env.example` to `.env` and fills in values
- **THEN** the documented variables (`DATABASE_URL`, `SECRET_KEY`) are sufficient
  to boot the app
