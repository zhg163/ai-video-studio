"""Tests for health check and root endpoints."""

import pytest


@pytest.mark.asyncio
async def test_healthz(client):
    response = await client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "ai-video-studio"
    assert data["version"] == "0.1.0"
