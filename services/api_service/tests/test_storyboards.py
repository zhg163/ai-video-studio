"""Integration tests for the Storyboard module.

Tests cover: generate (requires script), list, get, update, confirm — full lifecycle.
LLM calls are mocked; MongoDB + PostgreSQL are real (Docker).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from packages.common.mongo import get_mongo_db, Collections


# --- Mock Data ---

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
            "narration": "春天来了，万物复苏。",
            "dialogue": [],
            "subtitle": "春天来了",
        },
        {
            "section_no": 2,
            "title": "结尾",
            "narration": "让我们拥抱春天。",
            "dialogue": [],
            "subtitle": "拥抱春天",
        },
    ],
    "full_text": "春天来了，万物复苏。\n让我们拥抱春天。",
}

MOCK_STORYBOARD_RESULT = {
    "scenes": [
        {
            "scene_id": "scene_001",
            "title": "开场 - 春日花园",
            "summary": "展示春天花园的全景",
            "estimated_duration_sec": 10.0,
            "shots": [
                {
                    "shot_id": "shot_001",
                    "order_no": 1,
                    "shot_type": "wide",
                    "camera_movement": "push_in",
                    "character_desc": "",
                    "environment_desc": "一个鲜花盛开的花园",
                    "action_desc": "镜头缓缓推进到花园",
                    "voiceover_text": "春天来了，万物复苏。",
                    "image_prompt": "A beautiful spring garden with blooming flowers, sunlight, warm colors",
                    "video_prompt": "Slow push in shot of a spring garden with cherry blossoms",
                    "duration_sec": 5.0,
                    "status": "pending",
                    "selected_asset_ids": [],
                },
                {
                    "shot_id": "shot_002",
                    "order_no": 2,
                    "shot_type": "close",
                    "camera_movement": "static",
                    "character_desc": "",
                    "environment_desc": "花朵特写",
                    "action_desc": "阳光下花朵绽放",
                    "voiceover_text": "",
                    "image_prompt": "Close up of cherry blossom flowers in golden sunlight",
                    "video_prompt": "Close up shot of flowers blooming in sunlight",
                    "duration_sec": 5.0,
                    "status": "pending",
                    "selected_asset_ids": [],
                },
            ],
        },
        {
            "scene_id": "scene_002",
            "title": "结尾 - 拥抱春天",
            "summary": "温暖结尾",
            "estimated_duration_sec": 8.0,
            "shots": [
                {
                    "shot_id": "shot_003",
                    "order_no": 3,
                    "shot_type": "medium",
                    "camera_movement": "pull_out",
                    "character_desc": "一个人在花园中",
                    "environment_desc": "花园远景",
                    "action_desc": "镜头拉远，人物渐小",
                    "voiceover_text": "让我们拥抱春天。",
                    "image_prompt": "A person standing in a blooming garden, camera pulling out",
                    "video_prompt": "Pull out shot of person in flower garden, warm golden hour",
                    "duration_sec": 4.0,
                    "status": "pending",
                    "selected_asset_ids": [],
                },
            ],
        },
    ],
}


@pytest.fixture(autouse=True)
async def cleanup_storyboards():
    """Drop storyboard, script, and brief collections after each test."""
    yield
    try:
        mongo_db = get_mongo_db()
        await mongo_db[Collections.STORYBOARD].delete_many({})
        await mongo_db[Collections.SCRIPT].delete_many({})
        await mongo_db[Collections.CREATIVE_BRIEF].delete_many({})
    except Exception:
        pass


@pytest.fixture
async def script_for_storyboard(client, test_project) -> tuple[int, str]:
    """Create project + brief + script, return (project_id, script_id)."""
    project_id = test_project["id"]

    # Create brief
    with patch(
        "services.api_service.app.api.v1.briefs.CreativeAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_BRIEF_RESULT,
    ):
        brief_resp = await client.post(
            f"/api/v1/projects/{project_id}/briefs/generate",
            json={"text": "春天短视频"},
        )
    brief_id = brief_resp.json()["data"]["id"]

    # Create script
    with patch(
        "services.api_service.app.api.v1.scripts.ScriptAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_SCRIPT_RESULT,
    ):
        script_resp = await client.post(
            f"/api/v1/projects/{project_id}/scripts/generate",
            json={"brief_version_id": brief_id},
        )
    script_id = script_resp.json()["data"]["id"]

    return project_id, script_id


# --- Generate Storyboard ---

@pytest.mark.asyncio
async def test_generate_storyboard_success(client, script_for_storyboard):
    """Generate a storyboard from an existing script (LLM mocked)."""
    project_id, script_id = script_for_storyboard

    with patch(
        "services.api_service.app.api.v1.storyboards.StoryboardAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_STORYBOARD_RESULT,
    ):
        response = await client.post(
            f"/api/v1/projects/{project_id}/storyboards/generate",
            json={"script_version_id": script_id},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    sb = data["data"]
    assert sb["project_id"] == project_id
    assert sb["version_no"] == 1
    assert sb["script_version_id"] == script_id
    assert len(sb["scenes"]) == 2
    assert sb["scenes"][0]["title"] == "开场 - 春日花园"
    assert len(sb["scenes"][0]["shots"]) == 2
    assert sb["scenes"][0]["shots"][0]["shot_type"] == "wide"
    assert sb["scenes"][0]["shots"][0]["image_prompt"] != ""


@pytest.mark.asyncio
async def test_generate_storyboard_nonexistent_project(client):
    """Generate storyboard for non-existent project returns 404."""
    response = await client.post(
        "/api/v1/projects/99999/storyboards/generate",
        json={"script_version_id": "000000000000000000000000"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_storyboard_nonexistent_script(client, test_project):
    """Generate storyboard with non-existent script returns 404."""
    project_id = test_project["id"]
    response = await client.post(
        f"/api/v1/projects/{project_id}/storyboards/generate",
        json={"script_version_id": "000000000000000000000000"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_storyboard_invalid_script_id(client, test_project):
    """Generate storyboard with invalid script ID returns 404."""
    project_id = test_project["id"]
    response = await client.post(
        f"/api/v1/projects/{project_id}/storyboards/generate",
        json={"script_version_id": "invalid-id"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_storyboard_no_body(client, test_project):
    """Generate storyboard without request body fails validation."""
    project_id = test_project["id"]
    response = await client.post(f"/api/v1/projects/{project_id}/storyboards/generate")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_generate_storyboard_version_increments(client, script_for_storyboard):
    """Generating multiple storyboards increments version_no."""
    project_id, script_id = script_for_storyboard

    with patch(
        "services.api_service.app.api.v1.storyboards.StoryboardAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_STORYBOARD_RESULT,
    ):
        r1 = await client.post(
            f"/api/v1/projects/{project_id}/storyboards/generate",
            json={"script_version_id": script_id},
        )
        r2 = await client.post(
            f"/api/v1/projects/{project_id}/storyboards/generate",
            json={"script_version_id": script_id},
        )

    assert r1.json()["data"]["version_no"] == 1
    assert r2.json()["data"]["version_no"] == 2


# --- List Storyboards ---

@pytest.mark.asyncio
async def test_list_storyboards_empty(client, test_project):
    """List storyboards for a project with no storyboards."""
    project_id = test_project["id"]
    response = await client.get(f"/api/v1/projects/{project_id}/storyboards")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["items"] == []
    assert data["data"]["total"] == 0


@pytest.mark.asyncio
async def test_list_storyboards_with_data(client, script_for_storyboard):
    """List storyboards after generating some."""
    project_id, script_id = script_for_storyboard

    with patch(
        "services.api_service.app.api.v1.storyboards.StoryboardAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_STORYBOARD_RESULT,
    ):
        await client.post(
            f"/api/v1/projects/{project_id}/storyboards/generate",
            json={"script_version_id": script_id},
        )

    response = await client.get(f"/api/v1/projects/{project_id}/storyboards")
    data = response.json()
    assert data["data"]["total"] == 1
    assert len(data["data"]["items"]) == 1


# --- Get Storyboard ---

@pytest.mark.asyncio
async def test_get_storyboard_by_id(client, script_for_storyboard):
    """Get a specific storyboard by its MongoDB _id."""
    project_id, script_id = script_for_storyboard

    with patch(
        "services.api_service.app.api.v1.storyboards.StoryboardAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_STORYBOARD_RESULT,
    ):
        create_resp = await client.post(
            f"/api/v1/projects/{project_id}/storyboards/generate",
            json={"script_version_id": script_id},
        )

    sb_id = create_resp.json()["data"]["id"]
    response = await client.get(f"/api/v1/projects/{project_id}/storyboards/{sb_id}")
    assert response.status_code == 200
    assert len(response.json()["data"]["scenes"]) == 2


@pytest.mark.asyncio
async def test_get_storyboard_not_found(client, test_project):
    """Get non-existent storyboard returns 404."""
    project_id = test_project["id"]
    response = await client.get(
        f"/api/v1/projects/{project_id}/storyboards/000000000000000000000000"
    )
    assert response.status_code == 404


# --- Update Storyboard ---

@pytest.mark.asyncio
async def test_update_storyboard_scenes(client, script_for_storyboard):
    """Update scenes of an existing storyboard."""
    project_id, script_id = script_for_storyboard

    with patch(
        "services.api_service.app.api.v1.storyboards.StoryboardAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_STORYBOARD_RESULT,
    ):
        create_resp = await client.post(
            f"/api/v1/projects/{project_id}/storyboards/generate",
            json={"script_version_id": script_id},
        )

    sb_id = create_resp.json()["data"]["id"]
    new_scenes = [
        {
            "scene_id": "scene_001",
            "title": "新开场",
            "summary": "修改后的开场",
            "estimated_duration_sec": 15.0,
            "shots": [
                {
                    "shot_id": "shot_001",
                    "order_no": 1,
                    "shot_type": "extreme_close",
                    "camera_movement": "dolly",
                    "character_desc": "",
                    "environment_desc": "花朵微距",
                    "action_desc": "微距拍摄花朵",
                    "voiceover_text": "春天来了",
                    "image_prompt": "Macro shot of spring flowers",
                    "video_prompt": "Macro dolly shot of flowers",
                    "duration_sec": 6.0,
                    "status": "pending",
                    "selected_asset_ids": [],
                },
            ],
        },
    ]
    response = await client.put(
        f"/api/v1/projects/{project_id}/storyboards/{sb_id}",
        json={"scenes": new_scenes},
    )
    assert response.status_code == 200
    assert len(response.json()["data"]["scenes"]) == 1
    assert response.json()["data"]["scenes"][0]["title"] == "新开场"


@pytest.mark.asyncio
async def test_update_storyboard_empty_body(client, script_for_storyboard):
    """Update with empty body returns current storyboard unchanged."""
    project_id, script_id = script_for_storyboard

    with patch(
        "services.api_service.app.api.v1.storyboards.StoryboardAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_STORYBOARD_RESULT,
    ):
        create_resp = await client.post(
            f"/api/v1/projects/{project_id}/storyboards/generate",
            json={"script_version_id": script_id},
        )

    sb_id = create_resp.json()["data"]["id"]
    response = await client.put(
        f"/api/v1/projects/{project_id}/storyboards/{sb_id}",
        json={},
    )
    assert response.status_code == 200
    assert len(response.json()["data"]["scenes"]) == 2


@pytest.mark.asyncio
async def test_update_storyboard_not_found(client, test_project):
    """Update non-existent storyboard returns 404."""
    project_id = test_project["id"]
    response = await client.put(
        f"/api/v1/projects/{project_id}/storyboards/000000000000000000000000",
        json={"scenes": []},
    )
    assert response.status_code == 404


# --- Confirm Storyboard ---

@pytest.mark.asyncio
async def test_confirm_storyboard(client, script_for_storyboard):
    """Confirm a storyboard updates project's current_storyboard_version_id."""
    project_id, script_id = script_for_storyboard

    with patch(
        "services.api_service.app.api.v1.storyboards.StoryboardAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_STORYBOARD_RESULT,
    ):
        create_resp = await client.post(
            f"/api/v1/projects/{project_id}/storyboards/generate",
            json={"script_version_id": script_id},
        )

    sb_id = create_resp.json()["data"]["id"]
    response = await client.post(
        f"/api/v1/projects/{project_id}/storyboards/{sb_id}/confirm"
    )
    assert response.status_code == 200
    assert response.json()["code"] == 0

    # Verify project was updated
    proj_resp = await client.get(f"/api/v1/projects/{project_id}")
    proj_data = proj_resp.json()["data"]
    assert proj_data["current_storyboard_version_id"] is not None
    assert proj_data["status"] == "storyboard_confirmed"


@pytest.mark.asyncio
async def test_confirm_storyboard_not_found(client, test_project):
    """Confirm non-existent storyboard returns 404."""
    project_id = test_project["id"]
    response = await client.post(
        f"/api/v1/projects/{project_id}/storyboards/000000000000000000000000/confirm"
    )
    assert response.status_code == 404


# --- Full Lifecycle ---

@pytest.mark.asyncio
async def test_storyboard_full_lifecycle(client, script_for_storyboard):
    """Full lifecycle: generate -> list -> get -> update -> confirm."""
    project_id, script_id = script_for_storyboard

    # 1. Generate
    with patch(
        "services.api_service.app.api.v1.storyboards.StoryboardAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_STORYBOARD_RESULT,
    ):
        gen_resp = await client.post(
            f"/api/v1/projects/{project_id}/storyboards/generate",
            json={"script_version_id": script_id},
        )
    assert gen_resp.status_code == 200
    sb_id = gen_resp.json()["data"]["id"]

    # 2. List
    list_resp = await client.get(f"/api/v1/projects/{project_id}/storyboards")
    assert list_resp.json()["data"]["total"] == 1

    # 3. Get
    get_resp = await client.get(f"/api/v1/projects/{project_id}/storyboards/{sb_id}")
    assert get_resp.status_code == 200
    assert len(get_resp.json()["data"]["scenes"]) == 2

    # 4. Update - modify a scene
    updated_scenes = get_resp.json()["data"]["scenes"]
    updated_scenes[0]["title"] = "修改后的开场"
    update_resp = await client.put(
        f"/api/v1/projects/{project_id}/storyboards/{sb_id}",
        json={"scenes": updated_scenes},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["scenes"][0]["title"] == "修改后的开场"

    # 5. Confirm
    confirm_resp = await client.post(
        f"/api/v1/projects/{project_id}/storyboards/{sb_id}/confirm"
    )
    assert confirm_resp.status_code == 200

    # 6. Verify project state
    proj_resp = await client.get(f"/api/v1/projects/{project_id}")
    assert proj_resp.json()["data"]["current_storyboard_version_id"] is not None
    assert proj_resp.json()["data"]["status"] == "storyboard_confirmed"
