"""Health-check integration tests (app-foundation capability).

The /health endpoint runs ``SELECT 1`` against the database, so these exercise
the real app↔database path and run against Postgres via the ``pg_client``
fixture. They skip when no database is reachable.
"""

from __future__ import annotations


def test_health_ok(pg_client):
    """Health endpoint returns 200 when the database is reachable."""
    resp = pg_client.get("/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_index_is_health(pg_client):
    """Root route also serves the health check."""
    assert pg_client.get("/").status_code == 200
