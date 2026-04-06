"""Integration tests for the Shot media generation module.

Tests cover: get shot, update shot, list assets, generate image, generate video.
External API calls (GPT Image, Kling) are mocked; PostgreSQL + MongoDB are real.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from packages.common.mongo import Collections, get_mongo_db


MOCK_STORYBOARD = {
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
                    "image_prompt": "A beautiful spring garden with blooming flowers",
                    "video_prompt": "Slow push in shot of a spring garden",
                    "duration_sec": 5.0,
                    "status": "pending",
                    "selected_asset_ids": [],
                },
            ],
        },
    ],
}


MOCK_BRIEF = {
    "source_input": {"text": "春天短视频", "references": []},
    "structured_brief": {
        "goal": "展示春天的美好景色",
        "audience": "年轻人",
        "duration_sec": 30,
        "aspect_ratio": "16:9",
        "language": "zh-CN",
        "style": "温馨治愈",
        "platform": "抖音",
    },
    "constraints": {"must_include": ["花朵"], "must_not": [], "max_duration_sec": 60},
}

MOCK_SCRIPT = {
    "title": "春天的故事",
    "language": "zh-CN",
    "sections": [
        {"section_no": 1, "title": "开场", "narration": "春天来了", "dialogue": [], "subtitle": "春天来了"}
    ],
    "full_text": "春天来了",
}


@pytest.fixture(autouse=True)
async def cleanup():
    """Clean up MongoDB collections after each test."""
    yield
    mongo_db = get_mongo_db()
    await mongo_db[Collections.STORYBOARD].delete_many({})
    await mongo_db[Collections.SCRIPT].delete_many({})
    await mongo_db[Collections.CREATIVE_BRIEF].delete_many({})


@pytest.fixture
async def storyboard_with_shot(client, test_project) -> tuple[int, str]:
    """Create project + brief + script + storyboard, return (project_id, shot_id)."""
    project_id = test_project["id"]

    # Create brief
    with patch(
        "services.api_service.app.api.v1.briefs.CreativeAgent.run",
        new_callable=AsyncMock,
        return_value=MOCK_BRIEF,
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
        return_value=MOCK_SCRIPT,
    ):
        script_resp = await client.post(
            f"/api/v1/projects/{project_id}/scripts/generate",
            json={"brief_version_id": brief_id},
        )
    script_id = script_resp.json()["data"]["id"]

    # Create storyboard (mocked)
    mongo_db = get_mongo_db()
    await mongo_db[Collections.STORYBOARD].insert_one({
        "project_id": project_id,
        "version_no": 1,
        "script_version_id": script_id,
        "scenes": MOCK_STORYBOARD["scenes"],
    })

    return project_id, "shot_001"


# --- GET Shot ---


@pytest.mark.asyncio
async def test_get_shot_success(client, storyboard_with_shot):
    """Get shot details from storyboard."""
    project_id, shot_id = storyboard_with_shot

    response = await client.get(f"/api/v1/projects/{project_id}/shots/{shot_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["shot_id"] == shot_id
    assert data["data"]["shot_type"] == "wide"
    assert data["data"]["image_prompt"] == "A beautiful spring garden with blooming flowers"


@pytest.mark.asyncio
async def test_get_shot_not_found(client, test_project):
    """Get non-existent shot returns 404."""
    project_id = test_project["id"]

    response = await client.get(f"/api/v1/projects/{project_id}/shots/nonexistent")

    assert response.status_code == 404


# --- UPDATE Shot ---


@pytest.mark.asyncio
async def test_update_shot_success(client, storyboard_with_shot):
    """Update shot fields."""
    project_id, shot_id = storyboard_with_shot

    response = await client.put(
        f"/api/v1/projects/{project_id}/shots/{shot_id}",
        json={"image_prompt": "Updated prompt", "duration_sec": 6.0},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["image_prompt"] == "Updated prompt"
    assert data["data"]["duration_sec"] == 6.0


@pytest.mark.asyncio
async def test_update_shot_not_found(client, test_project):
    """Update non-existent shot returns 404."""
    project_id = test_project["id"]

    response = await client.put(
        f"/api/v1/projects/{project_id}/shots/nonexistent",
        json={"image_prompt": "test"},
    )

    assert response.status_code == 404


# --- LIST Assets ---


@pytest.mark.asyncio
async def test_list_shot_assets_empty(client, storyboard_with_shot):
    """List assets for a shot with no assets returns empty list."""
    project_id, shot_id = storyboard_with_shot

    response = await client.get(f"/api/v1/projects/{project_id}/shots/{shot_id}/assets")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["items"] == []


# --- GENERATE Image ---


@pytest.mark.asyncio
async def test_generate_image_success(client, storyboard_with_shot):
    """Generate keyframe image for a shot (mocked)."""
    project_id, shot_id = storyboard_with_shot

    # Mock GPTImageGateway to return fake image bytes
    mock_image_bytes = b"\x89PNG\r\n\x1a\nfake_image_data"

    with patch(
        "services.api_service.app.api.v1.shots.GPTImageGateway.generate",
        new_callable=AsyncMock,
        return_value=[mock_image_bytes],
    ):
        with patch(
            "services.api_service.app.api.v1.shots.upload_bytes",
            return_value="test_key",
        ):
            response = await client.post(
                f"/api/v1/projects/{project_id}/shots/{shot_id}/images/generate",
                json={"image_model": "gpt-image-1", "candidate_count": 1},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["task_type"] == "image_generation"
    assert data["data"]["status"] == "completed"


@pytest.mark.asyncio
async def test_generate_image_no_shot(client, test_project):
    """Generate image for non-existent shot returns 404."""
    project_id = test_project["id"]

    response = await client.post(
        f"/api/v1/projects/{project_id}/shots/nonexistent/images/generate",
        json={"image_model": "gpt-image-1"},
    )

    assert response.status_code == 404


# --- GENERATE Video ---


@pytest.mark.asyncio
async def test_generate_video_success(client, storyboard_with_shot):
    """Generate video for a shot (mocked)."""
    project_id, shot_id = storyboard_with_shot

    with patch(
        "services.api_service.app.api.v1.shots.KlingVideoGateway.submit_task",
        new_callable=AsyncMock,
        return_value="kling_task_123",
    ):
        with patch(
            "services.api_service.app.api.v1.shots.KlingVideoGateway.query_task",
            new_callable=AsyncMock,
            return_value=type("VideoTaskResult", (), {
                "task_id": "kling_task_123",
                "status": "succeed",
                "video_url": "http://example.com/video.mp4",
                "duration_sec": 5.0,
            })(),
        ):
            with patch(
                "services.api_service.app.api.v1.shots.KlingVideoGateway.download_video",
                new_callable=AsyncMock,
                return_value=b"fake_video_data",
            ):
                with patch(
                    "services.api_service.app.api.v1.shots.upload_bytes",
                    return_value="test_key",
                ):
                    with patch(
                        "services.api_service.app.api.v1.shots.get_presigned_url",
                        return_value="http://presigned.url",
                    ):
                        response = await client.post(
                            f"/api/v1/projects/{project_id}/shots/{shot_id}/videos/generate",
                            json={
                                "video_model": "kling-v1",
                                "input_mode": "text_to_video",
                                "duration_sec": 5.0,
                            },
                        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["task_type"] == "video_generation"


@pytest.mark.asyncio
async def test_generate_video_image_mode_requires_asset(client, storyboard_with_shot):
    """Generate video with image_to_video mode requires image_asset_id."""
    project_id, shot_id = storyboard_with_shot

    response = await client.post(
        f"/api/v1/projects/{project_id}/shots/{shot_id}/videos/generate",
        json={
            "video_model": "kling-v1",
            "input_mode": "image_to_video",
            "duration_sec": 5.0,
        },
    )

    assert response.status_code == 422


# --- DELETE Shot ---


@pytest.mark.asyncio
async def test_delete_shot_success(client, storyboard_with_shot):
    """Delete a shot from storyboard."""
    project_id, shot_id = storyboard_with_shot

    response = await client.delete(f"/api/v1/projects/{project_id}/shots/{shot_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0

    # Verify shot is removed
    get_resp = await client.get(f"/api/v1/projects/{project_id}/shots/{shot_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_shot_not_found(client, test_project):
    """Delete non-existent shot returns 404."""
    project_id = test_project["id"]

    response = await client.delete(f"/api/v1/projects/{project_id}/shots/nonexistent")

    assert response.status_code == 404