"""Integration tests for the Audio / TTS module.

Tests cover:
  - Batch voiceover generation (all shots in a storyboard)
  - Single-shot voiceover generation
  - List voiceover assets
  - Error handling (empty text, missing shot, missing storyboard)

External API calls (QwenTTSGateway) are mocked; PostgreSQL + MongoDB are real.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from packages.common.mongo import Collections, get_mongo_db


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

MOCK_STORYBOARD_SCENES = [
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
                "image_prompt": "A beautiful spring garden",
                "video_prompt": "Slow push in shot",
                "duration_sec": 5.0,
                "status": "pending",
                "selected_asset_ids": [],
            },
            {
                "shot_id": "shot_002",
                "order_no": 2,
                "shot_type": "close_up",
                "camera_movement": "static",
                "character_desc": "",
                "environment_desc": "花朵特写",
                "action_desc": "特写花朵绽放",
                "voiceover_text": "花朵竞相开放，争奇斗艳。",
                "image_prompt": "Close up of blooming flowers",
                "video_prompt": "Static shot of flowers",
                "duration_sec": 4.0,
                "status": "pending",
                "selected_asset_ids": [],
            },
        ],
    },
    {
        "scene_id": "scene_002",
        "title": "结尾",
        "summary": "总结",
        "estimated_duration_sec": 5.0,
        "shots": [
            {
                "shot_id": "shot_003",
                "order_no": 3,
                "shot_type": "wide",
                "camera_movement": "pull_out",
                "character_desc": "",
                "environment_desc": "全景",
                "action_desc": "镜头拉远",
                "voiceover_text": "",
                "image_prompt": "Wide garden shot",
                "video_prompt": "Pull out shot",
                "duration_sec": 3.0,
                "status": "pending",
                "selected_asset_ids": [],
            },
        ],
    },
]

MOCK_AUDIO_BYTES = b"ID3\x04\x00\x00\x00\x00\x00\x00fake_mp3_audio_data_for_testing"


@pytest.fixture(autouse=True)
async def cleanup():
    """Clean up MongoDB collections after each test."""
    yield
    mongo_db = get_mongo_db()
    await mongo_db[Collections.STORYBOARD].delete_many({})
    await mongo_db[Collections.SCRIPT].delete_many({})
    await mongo_db[Collections.CREATIVE_BRIEF].delete_many({})


@pytest.fixture
async def project_with_storyboard(client, test_project) -> tuple[int, str]:
    """Create project + brief + script + storyboard, return (project_id, storyboard_id)."""
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

    # Insert storyboard directly into MongoDB
    mongo_db = get_mongo_db()
    result = await mongo_db[Collections.STORYBOARD].insert_one({
        "project_id": project_id,
        "version_no": 1,
        "script_version_id": script_id,
        "scenes": MOCK_STORYBOARD_SCENES,
    })

    storyboard_id = str(result.inserted_id)
    return project_id, storyboard_id


# ---------------------------------------------------------------------------
# Batch Voiceover Generation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_batch_voiceover_success(client, project_with_storyboard):
    """Batch generate voiceover for all shots — 2 with text, 1 skipped."""
    project_id, storyboard_id = project_with_storyboard

    with patch(
        "services.api_service.app.api.v1.audio.QwenTTSGateway.synthesize",
        new_callable=AsyncMock,
        return_value=MOCK_AUDIO_BYTES,
    ):
        with patch(
            "services.api_service.app.api.v1.audio.upload_bytes",
            return_value="test_key",
        ):
            response = await client.post(
                f"/api/v1/projects/{project_id}/audio/generate-voiceover",
                json={
                    "storyboard_version_id": storyboard_id,
                    "voice_name": "alloy",
                    "speed": 1.0,
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0

    batch = data["data"]
    assert batch["project_id"] == project_id
    assert batch["storyboard_version_id"] == storyboard_id
    assert batch["total"] == 3
    assert batch["completed"] == 2  # shot_001 and shot_002 have text
    assert batch["skipped"] == 1   # shot_003 has empty voiceover_text
    assert batch["failed"] == 0

    # Check individual results
    results = batch["results"]
    assert results[0]["shot_id"] == "shot_001"
    assert results[0]["status"] == "completed"
    assert results[0]["asset_id"] is not None

    assert results[1]["shot_id"] == "shot_002"
    assert results[1]["status"] == "completed"
    assert results[1]["asset_id"] is not None

    assert results[2]["shot_id"] == "shot_003"
    assert results[2]["status"] == "skipped"
    assert results[2]["asset_id"] is None


@pytest.mark.asyncio
async def test_batch_voiceover_storyboard_not_found(client, test_project):
    """Batch voiceover with non-existent storyboard returns 404."""
    project_id = test_project["id"]

    response = await client.post(
        f"/api/v1/projects/{project_id}/audio/generate-voiceover",
        json={
            "storyboard_version_id": "000000000000000000000000",
            "voice_name": "alloy",
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_batch_voiceover_tts_failure(client, project_with_storyboard):
    """Batch voiceover handles TTS gateway failures gracefully."""
    project_id, storyboard_id = project_with_storyboard

    with patch(
        "services.api_service.app.api.v1.audio.QwenTTSGateway.synthesize",
        new_callable=AsyncMock,
        side_effect=RuntimeError("TTS API unavailable"),
    ):
        response = await client.post(
            f"/api/v1/projects/{project_id}/audio/generate-voiceover",
            json={
                "storyboard_version_id": storyboard_id,
                "voice_name": "alloy",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0

    batch = data["data"]
    assert batch["failed"] == 2   # shot_001, shot_002 failed
    assert batch["skipped"] == 1  # shot_003 skipped (empty text)
    assert batch["completed"] == 0

    # Check error messages
    assert batch["results"][0]["status"] == "failed"
    assert "TTS API unavailable" in batch["results"][0]["error"]


@pytest.mark.asyncio
async def test_batch_voiceover_custom_speed(client, project_with_storyboard):
    """Batch voiceover respects custom speed parameter."""
    project_id, storyboard_id = project_with_storyboard

    mock_synthesize = AsyncMock(return_value=MOCK_AUDIO_BYTES)

    with patch(
        "services.api_service.app.api.v1.audio.QwenTTSGateway.synthesize",
        mock_synthesize,
    ):
        with patch(
            "services.api_service.app.api.v1.audio.upload_bytes",
            return_value="test_key",
        ):
            response = await client.post(
                f"/api/v1/projects/{project_id}/audio/generate-voiceover",
                json={
                    "storyboard_version_id": storyboard_id,
                    "voice_name": "echo",
                    "speed": 1.5,
                },
            )

    assert response.status_code == 200

    # Verify synthesize was called with correct params
    assert mock_synthesize.call_count == 2  # 2 shots with text
    call_args = mock_synthesize.call_args_list[0]
    assert call_args.kwargs["voice"] == "echo"
    assert call_args.kwargs["speed"] == 1.5


# ---------------------------------------------------------------------------
# Single Shot Voiceover Generation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_single_shot_voiceover_success(client, project_with_storyboard):
    """Generate voiceover for a single shot."""
    project_id, storyboard_id = project_with_storyboard

    with patch(
        "services.api_service.app.api.v1.audio.QwenTTSGateway.synthesize",
        new_callable=AsyncMock,
        return_value=MOCK_AUDIO_BYTES,
    ):
        with patch(
            "services.api_service.app.api.v1.audio.upload_bytes",
            return_value="test_key",
        ):
            response = await client.post(
                f"/api/v1/projects/{project_id}/shots/shot_001/audios/generate",
                json={"voice_name": "alloy", "speed": 1.0},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["task_type"] == "voiceover_generate"
    assert data["data"]["status"] == "completed"
    assert data["data"]["model_provider"] == "qwen"
    assert data["data"]["model_name"] == "qwen3-tts"


@pytest.mark.asyncio
async def test_single_shot_voiceover_with_text_override(client, project_with_storyboard):
    """Generate voiceover with text_override replaces shot's voiceover_text."""
    project_id, storyboard_id = project_with_storyboard

    mock_synthesize = AsyncMock(return_value=MOCK_AUDIO_BYTES)

    with patch(
        "services.api_service.app.api.v1.audio.QwenTTSGateway.synthesize",
        mock_synthesize,
    ):
        with patch(
            "services.api_service.app.api.v1.audio.upload_bytes",
            return_value="test_key",
        ):
            response = await client.post(
                f"/api/v1/projects/{project_id}/shots/shot_001/audios/generate",
                json={
                    "voice_name": "fable",
                    "speed": 0.8,
                    "text_override": "这是自定义旁白文本。",
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["status"] == "completed"

    # Verify synthesize was called with the override text
    mock_synthesize.assert_called_once_with(
        text="这是自定义旁白文本。",
        voice="fable",
        speed=0.8,
    )


@pytest.mark.asyncio
async def test_single_shot_voiceover_empty_text(client, project_with_storyboard):
    """Generate voiceover for shot with empty voiceover_text returns 422."""
    project_id, storyboard_id = project_with_storyboard

    response = await client.post(
        f"/api/v1/projects/{project_id}/shots/shot_003/audios/generate",
        json={"voice_name": "alloy"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_single_shot_voiceover_not_found(client, test_project):
    """Generate voiceover for non-existent shot returns 404."""
    project_id = test_project["id"]

    response = await client.post(
        f"/api/v1/projects/{project_id}/shots/nonexistent/audios/generate",
        json={"voice_name": "alloy"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_single_shot_voiceover_tts_failure(client, project_with_storyboard):
    """TTS gateway failure is captured in GenerationTask."""
    project_id, storyboard_id = project_with_storyboard

    with patch(
        "services.api_service.app.api.v1.audio.QwenTTSGateway.synthesize",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Connection refused"),
    ):
        response = await client.post(
            f"/api/v1/projects/{project_id}/shots/shot_001/audios/generate",
            json={"voice_name": "alloy"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["status"] == "failed"
    assert "Connection refused" in data["data"]["error_message"]


# ---------------------------------------------------------------------------
# List Voiceovers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_voiceovers_empty(client, test_project):
    """List voiceovers for a project with none returns empty list."""
    project_id = test_project["id"]

    response = await client.get(f"/api/v1/projects/{project_id}/audio/voiceovers")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["items"] == []
    assert data["data"]["total"] == 0


@pytest.mark.asyncio
async def test_list_voiceovers_after_generation(client, project_with_storyboard):
    """List voiceovers shows assets after batch generation."""
    project_id, storyboard_id = project_with_storyboard

    # Generate voiceovers first
    with patch(
        "services.api_service.app.api.v1.audio.QwenTTSGateway.synthesize",
        new_callable=AsyncMock,
        return_value=MOCK_AUDIO_BYTES,
    ):
        with patch(
            "services.api_service.app.api.v1.audio.upload_bytes",
            return_value="test_key",
        ):
            gen_resp = await client.post(
                f"/api/v1/projects/{project_id}/audio/generate-voiceover",
                json={
                    "storyboard_version_id": storyboard_id,
                    "voice_name": "alloy",
                },
            )
    assert gen_resp.status_code == 200

    # List voiceovers
    with patch(
        "services.api_service.app.api.v1.audio.get_presigned_url",
        return_value="http://presigned.url/audio.mp3",
    ):
        response = await client.get(f"/api/v1/projects/{project_id}/audio/voiceovers")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["total"] == 2  # shot_001 and shot_002
    assert len(data["data"]["items"]) == 2

    # Verify asset properties
    item = data["data"]["items"][0]
    assert item["asset_type"] == "audio"
    assert item["usage_type"] == "tts"
    assert item["mime_type"] == "audio/mpeg"
    assert item["presigned_url"] == "http://presigned.url/audio.mp3"


# ---------------------------------------------------------------------------
# Shot Status Updates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_voiceover_updates_shot_status(client, project_with_storyboard):
    """Successful voiceover generation updates shot status to 'ready'."""
    project_id, storyboard_id = project_with_storyboard

    with patch(
        "services.api_service.app.api.v1.audio.QwenTTSGateway.synthesize",
        new_callable=AsyncMock,
        return_value=MOCK_AUDIO_BYTES,
    ):
        with patch(
            "services.api_service.app.api.v1.audio.upload_bytes",
            return_value="test_key",
        ):
            await client.post(
                f"/api/v1/projects/{project_id}/shots/shot_001/audios/generate",
                json={"voice_name": "alloy"},
            )

    # Check shot status via get shot
    resp = await client.get(f"/api/v1/projects/{project_id}/shots/shot_001")
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "ready"


@pytest.mark.asyncio
async def test_voiceover_failure_updates_shot_status(client, project_with_storyboard):
    """Failed voiceover generation updates shot status to 'failed'."""
    project_id, storyboard_id = project_with_storyboard

    with patch(
        "services.api_service.app.api.v1.audio.QwenTTSGateway.synthesize",
        new_callable=AsyncMock,
        side_effect=RuntimeError("API error"),
    ):
        await client.post(
            f"/api/v1/projects/{project_id}/shots/shot_001/audios/generate",
            json={"voice_name": "alloy"},
        )

    # Check shot status
    resp = await client.get(f"/api/v1/projects/{project_id}/shots/shot_001")
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "failed"
