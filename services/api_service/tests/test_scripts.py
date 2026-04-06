"""Integration tests for the Script module.

Tests cover: generate (requires brief), list, get, update, confirm — full lifecycle.
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

MOCK_SCRIPT_RESULT = {
    "title": "春天的故事",
    "language": "zh-CN",
    "sections": [
        {
            "section_no": 1,
            "title": "开场",
            "narration": "春天来了，万物复苏，花朵在阳光下绽放。",
            "dialogue": [],
            "subtitle": "春天来了",
        },
        {
            "section_no": 2,
            "title": "展示",
            "narration": "走在乡间小路上，感受春风拂面的温暖。",
            "dialogue": [],
            "subtitle": "春风拂面",
        },
        {
            "section_no": 3,
            "title": "结尾",
            "narration": "让我们一起拥抱这美好的春天。",
            "dialogue": [],
            "subtitle": "拥抱春天",
        },
    ],
    "full_text": "春天来了，万物复苏，花朵在阳光下绽放。\n走在乡间小路上，感受春风拂面的温暖。\n让我们一起拥抱这美好的春天。",
}


@pytest.fixture(autouse=True)
async def cleanup_scripts():
    """Drop script and brief collections after each test."""
    yield
    try:
        mongo_db = get_mongo_db()
        await mongo_db[Collections.SCRIPT].delete_many({})
        await mongo_db[Collections.CREATIVE_BRIEF].delete_many({})
    except Exception:
        pass


@pytest.fixture
async def brief_for_script(client, test_project) -> tuple[int, str]:
    """Create a project with a brief and return (project_id, brief_id)."""
    project_id = test_project["id"]

    with patch(
        "services.api_service.app.api.v1.briefs.CreativeAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_BRIEF_RESULT,
    ):
        resp = await client.post(
            f"/api/v1/projects/{project_id}/briefs/generate",
            json={"text": "做一个关于春天的短视频"},
        )
    assert resp.status_code == 200
    brief_id = resp.json()["data"]["id"]
    return project_id, brief_id


# --- Generate Script ---

@pytest.mark.asyncio
async def test_generate_script_success(client, brief_for_script):
    """Generate a script from an existing brief (LLM mocked)."""
    project_id, brief_id = brief_for_script

    with patch(
        "services.api_service.app.api.v1.scripts.ScriptAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_SCRIPT_RESULT,
    ):
        response = await client.post(
            f"/api/v1/projects/{project_id}/scripts/generate",
            json={"brief_version_id": brief_id},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    script = data["data"]
    assert script["project_id"] == project_id
    assert script["version_no"] == 1
    assert script["brief_version_id"] == brief_id
    assert script["title"] == "春天的故事"
    assert len(script["sections"]) == 3
    assert script["sections"][0]["title"] == "开场"
    assert "春天来了" in script["full_text"]


@pytest.mark.asyncio
async def test_generate_script_nonexistent_project(client):
    """Generate script for non-existent project returns 404."""
    with patch(
        "services.api_service.app.api.v1.scripts.ScriptAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_SCRIPT_RESULT,
    ):
        response = await client.post(
            "/api/v1/projects/99999/scripts/generate",
            json={"brief_version_id": "000000000000000000000000"},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_script_nonexistent_brief(client, test_project):
    """Generate script with non-existent brief returns 404."""
    project_id = test_project["id"]

    response = await client.post(
        f"/api/v1/projects/{project_id}/scripts/generate",
        json={"brief_version_id": "000000000000000000000000"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_script_invalid_brief_id(client, test_project):
    """Generate script with invalid brief ID returns 404."""
    project_id = test_project["id"]

    response = await client.post(
        f"/api/v1/projects/{project_id}/scripts/generate",
        json={"brief_version_id": "not-valid"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_script_no_body(client, test_project):
    """Generate script with no request body fails validation."""
    project_id = test_project["id"]
    response = await client.post(f"/api/v1/projects/{project_id}/scripts/generate")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_generate_script_version_increments(client, brief_for_script):
    """Generating multiple scripts increments version_no."""
    project_id, brief_id = brief_for_script

    with patch(
        "services.api_service.app.api.v1.scripts.ScriptAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_SCRIPT_RESULT,
    ):
        r1 = await client.post(
            f"/api/v1/projects/{project_id}/scripts/generate",
            json={"brief_version_id": brief_id},
        )
        r2 = await client.post(
            f"/api/v1/projects/{project_id}/scripts/generate",
            json={"brief_version_id": brief_id},
        )

    assert r1.json()["data"]["version_no"] == 1
    assert r2.json()["data"]["version_no"] == 2


# --- List Scripts ---

@pytest.mark.asyncio
async def test_list_scripts_empty(client, test_project):
    """List scripts for a project with no scripts."""
    project_id = test_project["id"]
    response = await client.get(f"/api/v1/projects/{project_id}/scripts")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["items"] == []
    assert data["data"]["total"] == 0


@pytest.mark.asyncio
async def test_list_scripts_with_data(client, brief_for_script):
    """List scripts after generating some."""
    project_id, brief_id = brief_for_script

    with patch(
        "services.api_service.app.api.v1.scripts.ScriptAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_SCRIPT_RESULT,
    ):
        await client.post(
            f"/api/v1/projects/{project_id}/scripts/generate",
            json={"brief_version_id": brief_id},
        )
        await client.post(
            f"/api/v1/projects/{project_id}/scripts/generate",
            json={"brief_version_id": brief_id},
        )

    response = await client.get(f"/api/v1/projects/{project_id}/scripts")
    data = response.json()
    assert data["data"]["total"] == 2
    assert len(data["data"]["items"]) == 2
    # Sorted by version_no descending
    assert data["data"]["items"][0]["version_no"] == 2


# --- Get Script ---

@pytest.mark.asyncio
async def test_get_script_by_id(client, brief_for_script):
    """Get a specific script by its MongoDB _id."""
    project_id, brief_id = brief_for_script

    with patch(
        "services.api_service.app.api.v1.scripts.ScriptAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_SCRIPT_RESULT,
    ):
        create_resp = await client.post(
            f"/api/v1/projects/{project_id}/scripts/generate",
            json={"brief_version_id": brief_id},
        )

    script_id = create_resp.json()["data"]["id"]
    response = await client.get(f"/api/v1/projects/{project_id}/scripts/{script_id}")
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "春天的故事"


@pytest.mark.asyncio
async def test_get_script_not_found(client, test_project):
    """Get non-existent script returns 404."""
    project_id = test_project["id"]
    response = await client.get(
        f"/api/v1/projects/{project_id}/scripts/000000000000000000000000"
    )
    assert response.status_code == 404


# --- Update Script ---

@pytest.mark.asyncio
async def test_update_script_title(client, brief_for_script):
    """Update the title of an existing script."""
    project_id, brief_id = brief_for_script

    with patch(
        "services.api_service.app.api.v1.scripts.ScriptAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_SCRIPT_RESULT,
    ):
        create_resp = await client.post(
            f"/api/v1/projects/{project_id}/scripts/generate",
            json={"brief_version_id": brief_id},
        )

    script_id = create_resp.json()["data"]["id"]
    response = await client.put(
        f"/api/v1/projects/{project_id}/scripts/{script_id}",
        json={"title": "新标题：春天的旋律"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "新标题：春天的旋律"


@pytest.mark.asyncio
async def test_update_script_sections(client, brief_for_script):
    """Update sections of an existing script."""
    project_id, brief_id = brief_for_script

    with patch(
        "services.api_service.app.api.v1.scripts.ScriptAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_SCRIPT_RESULT,
    ):
        create_resp = await client.post(
            f"/api/v1/projects/{project_id}/scripts/generate",
            json={"brief_version_id": brief_id},
        )

    script_id = create_resp.json()["data"]["id"]
    new_sections = [
        {"section_no": 1, "title": "新开场", "narration": "新旁白", "dialogue": [], "subtitle": ""},
    ]
    response = await client.put(
        f"/api/v1/projects/{project_id}/scripts/{script_id}",
        json={"sections": new_sections},
    )
    assert response.status_code == 200
    assert len(response.json()["data"]["sections"]) == 1
    assert response.json()["data"]["sections"][0]["title"] == "新开场"


@pytest.mark.asyncio
async def test_update_script_empty_body(client, brief_for_script):
    """Update with empty body returns current script unchanged."""
    project_id, brief_id = brief_for_script

    with patch(
        "services.api_service.app.api.v1.scripts.ScriptAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_SCRIPT_RESULT,
    ):
        create_resp = await client.post(
            f"/api/v1/projects/{project_id}/scripts/generate",
            json={"brief_version_id": brief_id},
        )

    script_id = create_resp.json()["data"]["id"]
    response = await client.put(
        f"/api/v1/projects/{project_id}/scripts/{script_id}",
        json={},
    )
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "春天的故事"


@pytest.mark.asyncio
async def test_update_script_not_found(client, test_project):
    """Update non-existent script returns 404."""
    project_id = test_project["id"]
    response = await client.put(
        f"/api/v1/projects/{project_id}/scripts/000000000000000000000000",
        json={"title": "new"},
    )
    assert response.status_code == 404


# --- Confirm Script ---

@pytest.mark.asyncio
async def test_confirm_script(client, brief_for_script):
    """Confirm a script updates project's current_script_version_id."""
    project_id, brief_id = brief_for_script

    with patch(
        "services.api_service.app.api.v1.scripts.ScriptAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_SCRIPT_RESULT,
    ):
        create_resp = await client.post(
            f"/api/v1/projects/{project_id}/scripts/generate",
            json={"brief_version_id": brief_id},
        )

    script_id = create_resp.json()["data"]["id"]
    response = await client.post(
        f"/api/v1/projects/{project_id}/scripts/{script_id}/confirm"
    )
    assert response.status_code == 200
    assert response.json()["code"] == 0

    # Verify project was updated
    proj_resp = await client.get(f"/api/v1/projects/{project_id}")
    proj_data = proj_resp.json()["data"]
    assert proj_data["current_script_version_id"] is not None
    assert proj_data["status"] == "script_confirmed"


@pytest.mark.asyncio
async def test_confirm_script_not_found(client, test_project):
    """Confirm non-existent script returns 404."""
    project_id = test_project["id"]
    response = await client.post(
        f"/api/v1/projects/{project_id}/scripts/000000000000000000000000/confirm"
    )
    assert response.status_code == 404


# --- Full Lifecycle ---

@pytest.mark.asyncio
async def test_script_full_lifecycle(client, brief_for_script):
    """Full lifecycle: generate -> list -> get -> update -> confirm."""
    project_id, brief_id = brief_for_script

    # 1. Generate
    with patch(
        "services.api_service.app.api.v1.scripts.ScriptAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_SCRIPT_RESULT,
    ):
        gen_resp = await client.post(
            f"/api/v1/projects/{project_id}/scripts/generate",
            json={"brief_version_id": brief_id},
        )
    assert gen_resp.status_code == 200
    script_id = gen_resp.json()["data"]["id"]

    # 2. List
    list_resp = await client.get(f"/api/v1/projects/{project_id}/scripts")
    assert list_resp.json()["data"]["total"] == 1

    # 3. Get
    get_resp = await client.get(f"/api/v1/projects/{project_id}/scripts/{script_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["title"] == "春天的故事"

    # 4. Update
    update_resp = await client.put(
        f"/api/v1/projects/{project_id}/scripts/{script_id}",
        json={"title": "春日物语"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["title"] == "春日物语"

    # 5. Confirm
    confirm_resp = await client.post(
        f"/api/v1/projects/{project_id}/scripts/{script_id}/confirm"
    )
    assert confirm_resp.status_code == 200

    # 6. Verify project state
    proj_resp = await client.get(f"/api/v1/projects/{project_id}")
    assert proj_resp.json()["data"]["current_script_version_id"] is not None
    assert proj_resp.json()["data"]["status"] == "script_confirmed"
