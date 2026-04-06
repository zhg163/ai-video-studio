"""Tests for Script, Storyboard API route registration.

Script and Storyboard endpoints now require request body.
Detailed tests are in test_scripts.py and test_storyboards.py.
"""

import pytest


# --- Script endpoints ---

@pytest.mark.asyncio
async def test_generate_script_requires_body(client):
    """Script generate endpoint requires a request body with brief_version_id."""
    response = await client.post("/api/v1/projects/1/scripts/generate")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_scripts_endpoint(client):
    response = await client.get("/api/v1/projects/1/scripts")
    assert response.status_code == 200


# --- Storyboard endpoints ---

@pytest.mark.asyncio
async def test_generate_storyboard_requires_body(client):
    """Storyboard generate endpoint requires a request body with script_version_id."""
    response = await client.post("/api/v1/projects/1/storyboards/generate")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_storyboards_endpoint(client):
    response = await client.get("/api/v1/projects/1/storyboards")
    assert response.status_code == 200
