"""Integration tests for the Render/Export module.

Tests cover:
  - Create render task (success, timeline not found, FFmpeg failure)
  - List render tasks
  - Get render task detail
  - Download redirect
  - Render plan builder

External calls (FFmpeg, MinIO) are mocked; PostgreSQL + MongoDB are real.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from packages.common.mongo import Collections, get_mongo_db


MOCK_BRIEF = {
    "source_input": {"text": "测试项目", "references": []},
    "structured_brief": {
        "goal": "测试导出",
        "audience": "开发者",
        "duration_sec": 10,
        "aspect_ratio": "16:9",
        "language": "zh-CN",
        "style": "测试",
        "platform": "web",
    },
    "constraints": {"must_include": [], "must_not": [], "max_duration_sec": 60},
}

MOCK_SCRIPT = {
    "title": "测试脚本",
    "language": "zh-CN",
    "sections": [
        {"section_no": 1, "title": "开场", "narration": "测试", "dialogue": [], "subtitle": "测试"}
    ],
    "full_text": "测试",
}

MOCK_TIMELINE_DOC = {
    "tracks": [
        {
            "track_id": "video_main",
            "track_type": "video",
            "clips": [
                {
                    "clip_id": "clip_001",
                    "source_shot_id": "shot_001",
                    "source_asset_id": None,  # No real asset in test
                    "start_ms": 0,
                    "end_ms": 5000,
                    "offset_ms": 0,
                    "volume": None,
                    "speed": 1.0,
                },
                {
                    "clip_id": "clip_002",
                    "source_shot_id": "shot_002",
                    "source_asset_id": None,
                    "start_ms": 5000,
                    "end_ms": 9000,
                    "offset_ms": 0,
                    "volume": None,
                    "speed": 1.0,
                },
            ],
        },
    ],
    "subtitle_segments": [
        {"id": "sub_1", "start_ms": 0, "end_ms": 5000, "text": "第一段旁白"},
        {"id": "sub_2", "start_ms": 5000, "end_ms": 9000, "text": "第二段旁白"},
    ],
    "transitions": [],
    "duration_ms": 9000,
}

# Fake MP4 and PNG bytes for mocked output
FAKE_MP4_BYTES = b"\x00\x00\x00\x1cftypisom" + b"\x00" * 100
FAKE_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


@pytest.fixture(autouse=True)
async def cleanup():
    """Clean up MongoDB collections after each test."""
    yield
    mongo_db = get_mongo_db()
    await mongo_db[Collections.TIMELINE].delete_many({})
    await mongo_db[Collections.STORYBOARD].delete_many({})
    await mongo_db[Collections.SCRIPT].delete_many({})
    await mongo_db[Collections.CREATIVE_BRIEF].delete_many({})


@pytest.fixture
async def project_with_timeline(client, test_project) -> tuple[int, str]:
    """Create project + timeline, return (project_id, timeline_version_id)."""
    project_id = test_project["id"]

    # Insert timeline directly into MongoDB
    mongo_db = get_mongo_db()
    doc = {**MOCK_TIMELINE_DOC, "project_id": project_id, "version_no": 1}
    result = await mongo_db[Collections.TIMELINE].insert_one(doc)
    timeline_id = str(result.inserted_id)

    return project_id, timeline_id


# ---------------------------------------------------------------------------
# Helper to mock the render pipeline (FFmpeg + MinIO)
# ---------------------------------------------------------------------------


def _mock_render_pipeline():
    """Return a context manager stack that mocks FFmpeg and MinIO calls."""
    import contextlib

    @contextlib.contextmanager
    def mock_all():
        # Mock FFmpegRenderer.render to create a fake output file
        async def fake_render(self, plan):
            output_path = str(self.work_dir / "output.mp4")
            with open(output_path, "wb") as f:
                f.write(FAKE_MP4_BYTES)
            return output_path

        # Mock FFmpegRenderer.extract_cover
        async def fake_extract_cover(self, video_path, timestamp_ms=1000):
            cover_path = str(self.work_dir / "cover.png")
            with open(cover_path, "wb") as f:
                f.write(FAKE_PNG_BYTES)
            return cover_path

        with patch(
            "services.api_service.app.api.v1.renders.FFmpegRenderer.render",
            fake_render,
        ):
            with patch(
                "services.api_service.app.api.v1.renders.FFmpegRenderer.extract_cover",
                fake_extract_cover,
            ):
                with patch(
                    "services.api_service.app.api.v1.renders.upload_bytes",
                    return_value="test_key",
                ):
                    with patch(
                        "services.api_service.app.api.v1.renders.get_presigned_url",
                        return_value="http://minio.local/export/output.mp4",
                    ):
                        yield

    return mock_all()


# ---------------------------------------------------------------------------
# Create Render
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_render_success(client, project_with_timeline):
    """Create a render task successfully."""
    project_id, timeline_id = project_with_timeline

    with _mock_render_pipeline():
        response = await client.post(
            f"/api/v1/projects/{project_id}/renders",
            json={
                "timeline_version_id": timeline_id,
                "resolution": "1080p",
                "burn_subtitle": True,
                "format": "mp4",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["status"] == "success"
    assert data["data"]["progress"] == 100
    assert data["data"]["output_asset_id"] is not None
    assert data["data"]["render_profile"] == "1080p_mp4"
    assert data["data"]["output_url"] is not None


@pytest.mark.asyncio
async def test_create_render_720p_mov(client, project_with_timeline):
    """Create a render with different resolution and format."""
    project_id, timeline_id = project_with_timeline

    with _mock_render_pipeline():
        response = await client.post(
            f"/api/v1/projects/{project_id}/renders",
            json={
                "timeline_version_id": timeline_id,
                "resolution": "720p",
                "format": "mov",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["status"] == "success"
    assert data["data"]["render_profile"] == "720p_mov"


@pytest.mark.asyncio
async def test_create_render_timeline_not_found(client, test_project):
    """Create render with non-existent timeline returns 404."""
    project_id = test_project["id"]

    response = await client.post(
        f"/api/v1/projects/{project_id}/renders",
        json={
            "timeline_version_id": "000000000000000000000000",
            "resolution": "1080p",
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_render_invalid_timeline_id(client, test_project):
    """Create render with invalid timeline ID returns 404."""
    project_id = test_project["id"]

    response = await client.post(
        f"/api/v1/projects/{project_id}/renders",
        json={
            "timeline_version_id": "not_a_valid_oid",
            "resolution": "1080p",
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_render_project_not_found(client):
    """Create render for non-existent project returns 404."""
    response = await client.post(
        "/api/v1/projects/99999/renders",
        json={
            "timeline_version_id": "000000000000000000000000",
            "resolution": "1080p",
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_render_ffmpeg_failure(client, project_with_timeline):
    """FFmpeg failure is captured in the render task."""
    project_id, timeline_id = project_with_timeline

    with patch(
        "services.api_service.app.api.v1.renders.FFmpegRenderer.render",
        new_callable=AsyncMock,
        side_effect=RuntimeError("FFmpeg crashed: segfault"),
    ):
        response = await client.post(
            f"/api/v1/projects/{project_id}/renders",
            json={
                "timeline_version_id": timeline_id,
                "resolution": "1080p",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["status"] == "failed"
    assert "FFmpeg crashed" in data["data"]["error_message"]
    assert data["data"]["progress"] == 0


# ---------------------------------------------------------------------------
# List Renders
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_renders_empty(client, test_project):
    """List renders for a project with none returns empty list."""
    project_id = test_project["id"]

    response = await client.get(f"/api/v1/projects/{project_id}/renders")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["items"] == []
    assert data["data"]["total"] == 0


@pytest.mark.asyncio
async def test_list_renders_after_creation(client, project_with_timeline):
    """List renders shows tasks after creation."""
    project_id, timeline_id = project_with_timeline

    # Create a render first
    with _mock_render_pipeline():
        await client.post(
            f"/api/v1/projects/{project_id}/renders",
            json={"timeline_version_id": timeline_id, "resolution": "1080p"},
        )

    # List renders
    with patch(
        "services.api_service.app.api.v1.renders.get_presigned_url",
        return_value="http://minio.local/export/output.mp4",
    ):
        response = await client.get(f"/api/v1/projects/{project_id}/renders")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["total"] == 1
    assert len(data["data"]["items"]) == 1
    assert data["data"]["items"][0]["status"] == "success"


# ---------------------------------------------------------------------------
# Get Render
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_render_success(client, project_with_timeline):
    """Get a specific render task."""
    project_id, timeline_id = project_with_timeline

    # Create a render
    with _mock_render_pipeline():
        create_resp = await client.post(
            f"/api/v1/projects/{project_id}/renders",
            json={"timeline_version_id": timeline_id, "resolution": "1080p"},
        )
    render_id = create_resp.json()["data"]["id"]

    # Get it
    with patch(
        "services.api_service.app.api.v1.renders.get_presigned_url",
        return_value="http://minio.local/export/output.mp4",
    ):
        response = await client.get(
            f"/api/v1/projects/{project_id}/renders/{render_id}"
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["id"] == render_id
    assert data["data"]["status"] == "success"


@pytest.mark.asyncio
async def test_get_render_not_found(client, test_project):
    """Get non-existent render returns 404."""
    project_id = test_project["id"]

    response = await client.get(f"/api/v1/projects/{project_id}/renders/99999")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Download Redirect
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_download_render_success(client, project_with_timeline):
    """Download redirects to presigned URL."""
    project_id, timeline_id = project_with_timeline

    # Create a successful render
    with _mock_render_pipeline():
        create_resp = await client.post(
            f"/api/v1/projects/{project_id}/renders",
            json={"timeline_version_id": timeline_id, "resolution": "1080p"},
        )
    render_id = create_resp.json()["data"]["id"]

    # Download (follow_redirects=False to check the redirect)
    with patch(
        "services.api_service.app.api.v1.renders.get_presigned_url",
        return_value="http://minio.local/export/output.mp4",
    ):
        response = await client.get(
            f"/api/v1/projects/{project_id}/renders/{render_id}/download",
            follow_redirects=False,
        )

    assert response.status_code == 307
    assert "minio.local" in response.headers.get("location", "")


@pytest.mark.asyncio
async def test_download_render_not_completed(client, project_with_timeline):
    """Download of a failed render returns 422."""
    project_id, timeline_id = project_with_timeline

    # Create a failed render
    with patch(
        "services.api_service.app.api.v1.renders.FFmpegRenderer.render",
        new_callable=AsyncMock,
        side_effect=RuntimeError("fail"),
    ):
        create_resp = await client.post(
            f"/api/v1/projects/{project_id}/renders",
            json={"timeline_version_id": timeline_id, "resolution": "1080p"},
        )
    render_id = create_resp.json()["data"]["id"]

    response = await client.get(
        f"/api/v1/projects/{project_id}/renders/{render_id}/download"
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_download_render_not_found(client, test_project):
    """Download non-existent render returns 404."""
    project_id = test_project["id"]

    response = await client.get(
        f"/api/v1/projects/{project_id}/renders/99999/download"
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_render_invalid_resolution(client, test_project):
    """Create render with invalid resolution fails validation."""
    project_id = test_project["id"]

    response = await client.post(
        f"/api/v1/projects/{project_id}/renders",
        json={
            "timeline_version_id": "000000000000000000000000",
            "resolution": "invalid_res",
        },
    )

    assert response.status_code == 422
