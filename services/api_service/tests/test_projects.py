"""Integration tests for Project CRUD endpoints.

These tests run against a real PostgreSQL database (Docker).
"""

import pytest


@pytest.mark.asyncio
async def test_create_project(client):
    """Create a project and verify response structure."""
    response = await client.post(
        "/api/v1/projects",
        json={"name": "Test Movie", "description": "A test film", "aspect_ratio": "16:9", "language": "zh-CN"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    project = data["data"]
    assert project["name"] == "Test Movie"
    assert project["description"] == "A test film"
    assert project["aspect_ratio"] == "16:9"
    assert project["language"] == "zh-CN"
    assert project["status"] == "draft"
    assert project["id"] > 0


@pytest.mark.asyncio
async def test_create_project_minimal(client):
    """Create a project with only the required name field."""
    response = await client.post(
        "/api/v1/projects",
        json={"name": "Minimal Project"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Minimal Project"
    assert data["aspect_ratio"] == "16:9"  # default
    assert data["language"] == "zh-CN"  # default


@pytest.mark.asyncio
async def test_create_project_validation_error(client):
    """Missing required name field returns 422."""
    response = await client.post("/api/v1/projects", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_projects_empty(client):
    """List projects returns empty list when no projects exist (or some from other tests)."""
    response = await client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "items" in data["data"]
    assert "total" in data["data"]
    assert isinstance(data["data"]["items"], list)


@pytest.mark.asyncio
async def test_list_projects_with_data(client):
    """Create a project, then list should include it."""
    # Create
    create_resp = await client.post("/api/v1/projects", json={"name": "Listable Project"})
    assert create_resp.status_code == 200
    created_id = create_resp.json()["data"]["id"]

    # List
    response = await client.get("/api/v1/projects")
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    ids = [item["id"] for item in items]
    assert created_id in ids


@pytest.mark.asyncio
async def test_list_projects_pagination(client):
    """Verify pagination parameters work."""
    response = await client.get("/api/v1/projects?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["page"] == 1
    assert data["page_size"] == 5


@pytest.mark.asyncio
async def test_get_project_by_id(client):
    """Create, then get by ID."""
    create_resp = await client.post("/api/v1/projects", json={"name": "Get By ID"})
    project_id = create_resp.json()["data"]["id"]

    response = await client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == project_id
    assert data["name"] == "Get By ID"


@pytest.mark.asyncio
async def test_get_project_not_found(client):
    """Non-existent project returns 404."""
    response = await client.get("/api/v1/projects/999999")
    assert response.status_code == 404
    assert response.json()["code"] == 404


@pytest.mark.asyncio
async def test_update_project(client):
    """Create, then update name and description."""
    create_resp = await client.post("/api/v1/projects", json={"name": "Before Update"})
    project_id = create_resp.json()["data"]["id"]

    response = await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "After Update", "description": "Updated desc"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "After Update"
    assert data["description"] == "Updated desc"


@pytest.mark.asyncio
async def test_update_project_partial(client):
    """Partial update only changes specified fields."""
    create_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Partial", "description": "Original", "language": "en"},
    )
    project_id = create_resp.json()["data"]["id"]

    # Only update name, description and language should remain
    response = await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Partial Updated"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Partial Updated"
    assert data["description"] == "Original"
    assert data["language"] == "en"


@pytest.mark.asyncio
async def test_update_project_not_found(client):
    """Update non-existent project returns 404."""
    response = await client.patch("/api/v1/projects/999999", json={"name": "Nope"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_archive_project(client):
    """Create and archive a project."""
    create_resp = await client.post("/api/v1/projects", json={"name": "To Archive"})
    project_id = create_resp.json()["data"]["id"]

    response = await client.post(f"/api/v1/projects/{project_id}/archive")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "archived"


@pytest.mark.asyncio
async def test_archive_project_not_found(client):
    """Archive non-existent project returns 404."""
    response = await client.post("/api/v1/projects/999999/archive")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_project_full_lifecycle(client):
    """Full lifecycle: create -> get -> update -> archive -> verify."""
    # Create
    resp = await client.post(
        "/api/v1/projects",
        json={"name": "Lifecycle Test", "description": "Full cycle"},
    )
    assert resp.status_code == 200
    project_id = resp.json()["data"]["id"]

    # Get
    resp = await client.get(f"/api/v1/projects/{project_id}")
    assert resp.json()["data"]["status"] == "draft"

    # Update
    resp = await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Lifecycle Updated"},
    )
    assert resp.json()["data"]["name"] == "Lifecycle Updated"

    # Archive
    resp = await client.post(f"/api/v1/projects/{project_id}/archive")
    assert resp.json()["data"]["status"] == "archived"

    # Verify archived
    resp = await client.get(f"/api/v1/projects/{project_id}")
    assert resp.json()["data"]["status"] == "archived"


@pytest.mark.asyncio
async def test_nonexistent_route(client):
    """Truly nonexistent routes return 404."""
    response = await client.get("/api/v1/nonexistent")
    assert response.status_code == 404
