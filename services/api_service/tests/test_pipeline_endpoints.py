"""Tests for Brief, Script, Storyboard API route registration.

Brief endpoints now have real implementations, so we test route registration
via the new test_briefs.py. This file covers Script and Storyboard stubs only.
"""

import pytest


# --- Script endpoints ---

@pytest.mark.asyncio
async def test_generate_script_endpoint(client):
    response = await client.post("/api/v1/projects/1/scripts/generate")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "queued"


@pytest.mark.asyncio
async def test_list_scripts_endpoint(client):
    response = await client.get("/api/v1/projects/1/scripts")
    assert response.status_code == 200


# --- Storyboard endpoints ---

@pytest.mark.asyncio
async def test_generate_storyboard_endpoint(client):
    response = await client.post("/api/v1/projects/1/storyboards/generate")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "queued"


@pytest.mark.asyncio
async def test_list_storyboards_endpoint(client):
    response = await client.get("/api/v1/projects/1/storyboards")
    assert response.status_code == 200
