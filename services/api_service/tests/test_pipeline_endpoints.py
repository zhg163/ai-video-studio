"""Tests for Brief, Script, Storyboard API route registration."""

import pytest


# --- Brief endpoints ---

@pytest.mark.asyncio
async def test_generate_brief_endpoint(client):
    response = await client.post("/api/v1/projects/1/briefs/generate")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["status"] == "queued"


@pytest.mark.asyncio
async def test_list_briefs_endpoint(client):
    response = await client.get("/api/v1/projects/1/briefs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_confirm_brief_endpoint(client):
    response = await client.post("/api/v1/projects/1/briefs/v1/confirm")
    assert response.status_code == 200


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
