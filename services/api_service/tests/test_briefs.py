"""Integration tests for the Brief module.

Tests cover: generate, list, get, update, confirm — full lifecycle.
LLM calls are mocked; MongoDB + PostgreSQL are real (Docker).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from packages.common.mongo import get_mongo_db, Collections


# --- Helpers ---

MOCK_BRIEF_RESULT = {
    "source_input": {"text": "做一个关于春天的短视频", "references": []},
    "structured_brief": {
        "goal": "展示春天的美好景色",
        "audience": "年轻人",
        "duration_sec": 30,
        "aspect_ratio": "16:9",
        "language": "zh-CN",
        "style": "温馨治愈",
        "platform": "抖音",
    },
    "constraints": {
        "must_include": ["花朵", "阳光"],
        "must_not": ["暴力"],
        "max_duration_sec": 60,
    },
}


@pytest.fixture(autouse=True)
async def cleanup_briefs():
    """Drop brief collection before each test for isolation."""
    yield
    # Cleanup after test
    try:
        mongo_db = get_mongo_db()
        await mongo_db[Collections.CREATIVE_BRIEF].delete_many({})
    except Exception:
        pass


# --- Generate Brief ---

@pytest.mark.asyncio
async def test_generate_brief_success(client, test_project):
    """Generate a brief for an existing project (LLM mocked)."""
    project_id = test_project["id"]

    with patch(
        "services.api_service.app.api.v1.briefs.CreativeAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_BRIEF_RESULT,
    ):
        response = await client.post(
            f"/api/v1/projects/{project_id}/briefs/generate",
            json={"text": "做一个关于春天的短视频"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    brief = data["data"]
    assert brief["project_id"] == project_id
    assert brief["version_no"] == 1
    assert brief["structured_brief"]["goal"] == "展示春天的美好景色"
    assert brief["source_input"]["text"] == "做一个关于春天的短视频"
    assert brief["constraints"]["must_include"] == ["花朵", "阳光"]
    assert "id" in brief or "_id" in brief


@pytest.mark.asyncio
async def test_generate_brief_nonexistent_project(client):
    """Generate brief for a non-existent project returns 404."""
    with patch(
        "services.api_service.app.api.v1.briefs.CreativeAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_BRIEF_RESULT,
    ):
        response = await client.post(
            "/api/v1/projects/99999/briefs/generate",
            json={"text": "test"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_brief_empty_text(client, test_project):
    """Generate brief with empty text should fail validation."""
    project_id = test_project["id"]
    response = await client.post(
        f"/api/v1/projects/{project_id}/briefs/generate",
        json={"text": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_generate_brief_no_body(client, test_project):
    """Generate brief with no request body should fail."""
    project_id = test_project["id"]
    response = await client.post(
        f"/api/v1/projects/{project_id}/briefs/generate",
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_generate_brief_version_increments(client, test_project):
    """Generating multiple briefs should increment version_no."""
    project_id = test_project["id"]

    with patch(
        "services.api_service.app.api.v1.briefs.CreativeAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_BRIEF_RESULT,
    ):
        r1 = await client.post(
            f"/api/v1/projects/{project_id}/briefs/generate",
            json={"text": "第一版"},
        )
        r2 = await client.post(
            f"/api/v1/projects/{project_id}/briefs/generate",
            json={"text": "第二版"},
        )

    assert r1.json()["data"]["version_no"] == 1
    assert r2.json()["data"]["version_no"] == 2


# --- List Briefs ---

@pytest.mark.asyncio
async def test_list_briefs_empty(client, test_project):
    """List briefs for a project with no briefs returns empty."""
    project_id = test_project["id"]
    response = await client.get(f"/api/v1/projects/{project_id}/briefs")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["items"] == []
    assert data["data"]["total"] == 0


@pytest.mark.asyncio
async def test_list_briefs_with_data(client, test_project):
    """List briefs after generating some."""
    project_id = test_project["id"]

    with patch(
        "services.api_service.app.api.v1.briefs.CreativeAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_BRIEF_RESULT,
    ):
        await client.post(
            f"/api/v1/projects/{project_id}/briefs/generate",
            json={"text": "brief 1"},
        )
        await client.post(
            f"/api/v1/projects/{project_id}/briefs/generate",
            json={"text": "brief 2"},
        )

    response = await client.get(f"/api/v1/projects/{project_id}/briefs")
    data = response.json()
    assert data["data"]["total"] == 2
    assert len(data["data"]["items"]) == 2
    # Sorted by version_no descending
    assert data["data"]["items"][0]["version_no"] == 2
    assert data["data"]["items"][1]["version_no"] == 1


@pytest.mark.asyncio
async def test_list_briefs_pagination(client, test_project):
    """Pagination works for brief listing."""
    project_id = test_project["id"]

    with patch(
        "services.api_service.app.api.v1.briefs.CreativeAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_BRIEF_RESULT,
    ):
        for i in range(3):
            await client.post(
                f"/api/v1/projects/{project_id}/briefs/generate",
                json={"text": f"brief {i}"},
            )

    response = await client.get(
        f"/api/v1/projects/{project_id}/briefs?page=1&page_size=2"
    )
    data = response.json()
    assert data["data"]["total"] == 3
    assert len(data["data"]["items"]) == 2

    response2 = await client.get(
        f"/api/v1/projects/{project_id}/briefs?page=2&page_size=2"
    )
    data2 = response2.json()
    assert len(data2["data"]["items"]) == 1


# --- Get Brief ---

@pytest.mark.asyncio
async def test_get_brief_by_id(client, test_project):
    """Get a specific brief by its MongoDB _id."""
    project_id = test_project["id"]

    with patch(
        "services.api_service.app.api.v1.briefs.CreativeAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_BRIEF_RESULT,
    ):
        create_resp = await client.post(
            f"/api/v1/projects/{project_id}/briefs/generate",
            json={"text": "test brief"},
        )

    brief_id = create_resp.json()["data"]["id"]
    response = await client.get(
        f"/api/v1/projects/{project_id}/briefs/{brief_id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == brief_id
    assert data["data"]["version_no"] == 1


@pytest.mark.asyncio
async def test_get_brief_not_found(client, test_project):
    """Get a non-existent brief returns 404."""
    project_id = test_project["id"]
    # Valid ObjectId format but doesn't exist
    response = await client.get(
        f"/api/v1/projects/{project_id}/briefs/000000000000000000000000"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_brief_invalid_id(client, test_project):
    """Get a brief with invalid ObjectId returns 404."""
    project_id = test_project["id"]
    response = await client.get(
        f"/api/v1/projects/{project_id}/briefs/not-a-valid-id"
    )
    assert response.status_code == 404


# --- Update Brief ---

@pytest.mark.asyncio
async def test_update_brief(client, test_project):
    """Update structured_brief of an existing brief."""
    project_id = test_project["id"]

    with patch(
        "services.api_service.app.api.v1.briefs.CreativeAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_BRIEF_RESULT,
    ):
        create_resp = await client.post(
            f"/api/v1/projects/{project_id}/briefs/generate",
            json={"text": "original"},
        )

    brief_id = create_resp.json()["data"]["id"]
    updated_brief = {
        "structured_brief": {
            "goal": "修改后的目标",
            "audience": "中年人",
            "duration_sec": 45,
            "aspect_ratio": "9:16",
            "language": "zh-CN",
            "style": "科技感",
            "platform": "B站",
        }
    }
    response = await client.put(
        f"/api/v1/projects/{project_id}/briefs/{brief_id}",
        json=updated_brief,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["structured_brief"]["goal"] == "修改后的目标"
    assert data["data"]["structured_brief"]["style"] == "科技感"


@pytest.mark.asyncio
async def test_update_brief_constraints_only(client, test_project):
    """Update only constraints of an existing brief."""
    project_id = test_project["id"]

    with patch(
        "services.api_service.app.api.v1.briefs.CreativeAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_BRIEF_RESULT,
    ):
        create_resp = await client.post(
            f"/api/v1/projects/{project_id}/briefs/generate",
            json={"text": "original"},
        )

    brief_id = create_resp.json()["data"]["id"]
    response = await client.put(
        f"/api/v1/projects/{project_id}/briefs/{brief_id}",
        json={"constraints": {"must_include": ["新元素"], "must_not": [], "max_duration_sec": 120}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["constraints"]["must_include"] == ["新元素"]
    assert data["data"]["constraints"]["max_duration_sec"] == 120


@pytest.mark.asyncio
async def test_update_brief_empty_body(client, test_project):
    """Update with empty body returns current brief unchanged."""
    project_id = test_project["id"]

    with patch(
        "services.api_service.app.api.v1.briefs.CreativeAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_BRIEF_RESULT,
    ):
        create_resp = await client.post(
            f"/api/v1/projects/{project_id}/briefs/generate",
            json={"text": "original"},
        )

    brief_id = create_resp.json()["data"]["id"]
    response = await client.put(
        f"/api/v1/projects/{project_id}/briefs/{brief_id}",
        json={},
    )
    assert response.status_code == 200
    assert response.json()["data"]["structured_brief"]["goal"] == "展示春天的美好景色"


@pytest.mark.asyncio
async def test_update_brief_not_found(client, test_project):
    """Update a non-existent brief returns 404."""
    project_id = test_project["id"]
    response = await client.put(
        f"/api/v1/projects/{project_id}/briefs/000000000000000000000000",
        json={"structured_brief": {"goal": "new"}},
    )
    assert response.status_code == 404


# --- Confirm Brief ---

@pytest.mark.asyncio
async def test_confirm_brief(client, test_project):
    """Confirm a brief updates project's current_brief_version_id."""
    project_id = test_project["id"]

    with patch(
        "services.api_service.app.api.v1.briefs.CreativeAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_BRIEF_RESULT,
    ):
        create_resp = await client.post(
            f"/api/v1/projects/{project_id}/briefs/generate",
            json={"text": "confirm me"},
        )

    brief_id = create_resp.json()["data"]["id"]

    response = await client.post(
        f"/api/v1/projects/{project_id}/briefs/{brief_id}/confirm"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["version_no"] == 1

    # Verify the project was updated
    proj_resp = await client.get(f"/api/v1/projects/{project_id}")
    proj_data = proj_resp.json()["data"]
    assert proj_data["current_brief_version_id"] is not None
    assert proj_data["status"] == "brief_confirmed"


@pytest.mark.asyncio
async def test_confirm_brief_not_found(client, test_project):
    """Confirm a non-existent brief returns 404."""
    project_id = test_project["id"]
    response = await client.post(
        f"/api/v1/projects/{project_id}/briefs/000000000000000000000000/confirm"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_confirm_brief_nonexistent_project(client):
    """Confirm a brief for a non-existent project returns 404."""
    response = await client.post(
        "/api/v1/projects/99999/briefs/000000000000000000000000/confirm"
    )
    assert response.status_code == 404


# --- Full Lifecycle ---

@pytest.mark.asyncio
async def test_brief_full_lifecycle(client, test_project):
    """Full lifecycle: generate -> list -> get -> update -> confirm."""
    project_id = test_project["id"]

    # 1. Generate
    with patch(
        "services.api_service.app.api.v1.briefs.CreativeAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_BRIEF_RESULT,
    ):
        gen_resp = await client.post(
            f"/api/v1/projects/{project_id}/briefs/generate",
            json={"text": "lifecycle test"},
        )
    assert gen_resp.status_code == 200
    brief_id = gen_resp.json()["data"]["id"]

    # 2. List
    list_resp = await client.get(f"/api/v1/projects/{project_id}/briefs")
    assert list_resp.json()["data"]["total"] == 1

    # 3. Get
    get_resp = await client.get(
        f"/api/v1/projects/{project_id}/briefs/{brief_id}"
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["id"] == brief_id

    # 4. Update
    update_resp = await client.put(
        f"/api/v1/projects/{project_id}/briefs/{brief_id}",
        json={"structured_brief": {"goal": "updated goal", "audience": "全年龄",
                                     "duration_sec": 60, "aspect_ratio": "16:9",
                                     "language": "zh-CN", "style": "史诗大片",
                                     "platform": "YouTube"}},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["structured_brief"]["goal"] == "updated goal"

    # 5. Confirm
    confirm_resp = await client.post(
        f"/api/v1/projects/{project_id}/briefs/{brief_id}/confirm"
    )
    assert confirm_resp.status_code == 200

    # 6. Verify project state
    proj_resp = await client.get(f"/api/v1/projects/{project_id}")
    assert proj_resp.json()["data"]["current_brief_version_id"] is not None
