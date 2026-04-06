"""Tests for Project API endpoints (stub / no DB).

These tests verify route registration and error handling.
Without a running PostgreSQL, DB-dependent endpoints return 500 via the error handler.
"""

import pytest


@pytest.mark.asyncio
async def test_list_projects_endpoint_exists(client):
    """Verify the projects list endpoint is registered (returns 500 without DB, not 404)."""
    response = await client.get("/api/v1/projects")
    # Without a real DB, the global error handler catches and returns 500.
    assert response.status_code == 500
    data = response.json()
    assert data["code"] == 500
    assert "request_id" in data


@pytest.mark.asyncio
async def test_create_project_endpoint_exists(client):
    """Verify the project create endpoint is registered."""
    response = await client.post(
        "/api/v1/projects",
        json={"name": "Test Project"},
    )
    assert response.status_code == 500  # no DB
    assert response.json()["code"] == 500


@pytest.mark.asyncio
async def test_get_project_endpoint_exists(client):
    """Verify the project detail endpoint is registered."""
    response = await client.get("/api/v1/projects/1")
    assert response.status_code == 500  # no DB


@pytest.mark.asyncio
async def test_update_project_endpoint_exists(client):
    """Verify the project update endpoint is registered."""
    response = await client.patch(
        "/api/v1/projects/1",
        json={"name": "Updated"},
    )
    assert response.status_code == 500  # no DB


@pytest.mark.asyncio
async def test_archive_project_endpoint_exists(client):
    """Verify the project archive endpoint is registered."""
    response = await client.post("/api/v1/projects/1/archive")
    assert response.status_code == 500  # no DB


@pytest.mark.asyncio
async def test_project_nonexistent_route(client):
    """Verify that truly nonexistent routes return 404."""
    response = await client.get("/api/v1/nonexistent")
    assert response.status_code == 404
