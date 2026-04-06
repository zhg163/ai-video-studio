"""Shared test fixtures and conftest."""

import pytest
from httpx import ASGITransport, AsyncClient

from packages.common.database import reset_engine
from packages.common.mongo import reset_mongo
from services.api_service.app.main import create_app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async HTTP test client for the FastAPI app.

    Resets the DB engine and MongoDB client before creating the app to ensure
    connections are bound to the current event loop.
    """
    reset_engine()
    reset_mongo()
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_project(client: AsyncClient) -> dict:
    """Create a project and return its data dict.

    Useful for tests that need a valid project_id (e.g., brief, script endpoints).
    """
    response = await client.post(
        "/api/v1/projects",
        json={"name": "Test Project for Briefs", "description": "integration test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    return data["data"]
