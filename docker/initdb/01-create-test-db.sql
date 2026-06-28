-- Runs once, on first initialization of the Postgres data volume.
-- Creates the dedicated database integration tests build and tear down, so the
-- development database (clinicremind) is never wiped by a test run.
CREATE DATABASE clinicremind_test OWNER clinicremind;
