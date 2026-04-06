"""Integration tests for the Timeline module.

Tests cover: assemble, list, get, update, confirm, clip reorder, clip replace.
MongoDB is real (Docker); no external API mocking needed for timeline assembly.
"""

from __future__ import annotations

import pytest

from packages.common.mongo import Collections, get_mongo_db


# --- Shared test data ---

STORYBOARD_SCENES = [
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
                "image_prompt": "A spring garden",
                "video_prompt": "Push in shot of garden",
                "duration_sec": 5.0,
                "status": "video_ready",
                "selected_asset_ids": [101],
            },
            {
                "shot_id": "shot_002",
                "order_no": 2,
                "shot_type": "close",
                "camera_movement": "static",
                "character_desc": "",
                "environment_desc": "花朵特写",
                "action_desc": "阳光下花朵绽放",
                "voiceover_text": "花儿朵朵开。",
                "image_prompt": "Close up flowers",
                "video_prompt": "Close up of flowers",
                "duration_sec": 4.0,
                "status": "video_ready",
                "selected_asset_ids": [102],
            },
        ],
    },
    {
        "scene_id": "scene_002",
        "title": "结尾 - 拥抱春天",
        "summary": "温暖结尾",
        "estimated_duration_sec": 4.0,
        "shots": [
            {
                "shot_id": "shot_003",
                "order_no": 3,
                "shot_type": "medium",
                "camera_movement": "pull_out",
                "character_desc": "一个人在花园中",
                "environment_desc": "花园远景",
                "action_desc": "镜头拉远",
                "voiceover_text": "让我们拥抱春天。",
                "image_prompt": "Person in garden",
                "video_prompt": "Pull out shot",
                "duration_sec": 4.0,
                "status": "video_ready",
                "selected_asset_ids": [103],
            },
        ],
    },
]


@pytest.fixture(autouse=True)
async def cleanup():
    """Clean up MongoDB collections after each test."""
    yield
    try:
        mongo_db = get_mongo_db()
        await mongo_db[Collections.TIMELINE].delete_many({})
        await mongo_db[Collections.STORYBOARD].delete_many({})
    except Exception:
        pass


@pytest.fixture
async def storyboard_id(client, test_project) -> tuple[int, str]:
    """Create a project + storyboard, return (project_id, storyboard_id)."""
    project_id = test_project["id"]
    mongo_db = get_mongo_db()
    result = await mongo_db[Collections.STORYBOARD].insert_one({
        "project_id": project_id,
        "version_no": 1,
        "script_version_id": "dummy_script",
        "scenes": STORYBOARD_SCENES,
    })
    return project_id, str(result.inserted_id)


@pytest.fixture
async def timeline_id(client, storyboard_id) -> tuple[int, str, str]:
    """Assemble a timeline and return (project_id, storyboard_id, timeline_id)."""
    project_id, sb_id = storyboard_id
    resp = await client.post(
        f"/api/v1/projects/{project_id}/timelines/assemble",
        json={"storyboard_version_id": sb_id},
    )
    assert resp.status_code == 200
    tl_id = resp.json()["data"]["id"]
    return project_id, sb_id, tl_id


# ===== ASSEMBLE =====


@pytest.mark.asyncio
async def test_assemble_timeline_success(client, storyboard_id):
    """Assemble a timeline from a storyboard with 3 shots."""
    project_id, sb_id = storyboard_id

    resp = await client.post(
        f"/api/v1/projects/{project_id}/timelines/assemble",
        json={"storyboard_version_id": sb_id},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    tl = data["data"]
    assert tl["project_id"] == project_id
    assert tl["version_no"] == 1
    assert tl["storyboard_version_id"] == sb_id

    # Should have 1 video track with 3 clips
    assert len(tl["tracks"]) == 1
    video_track = tl["tracks"][0]
    assert video_track["track_type"] == "video"
    assert len(video_track["clips"]) == 3

    # Verify clip timing: 5s + 4s + 4s = 13s = 13000ms
    clips = video_track["clips"]
    assert clips[0]["start_ms"] == 0
    assert clips[0]["end_ms"] == 5000
    assert clips[0]["source_shot_id"] == "shot_001"
    assert clips[0]["source_asset_id"] == 101

    assert clips[1]["start_ms"] == 5000
    assert clips[1]["end_ms"] == 9000
    assert clips[1]["source_shot_id"] == "shot_002"

    assert clips[2]["start_ms"] == 9000
    assert clips[2]["end_ms"] == 13000
    assert clips[2]["source_shot_id"] == "shot_003"

    # Duration
    assert tl["duration_ms"] == 13000

    # Subtitles auto-generated from voiceover_text
    assert len(tl["subtitle_segments"]) == 3
    assert tl["subtitle_segments"][0]["text"] == "春天来了，万物复苏。"

    # No transitions by default (cut)
    assert len(tl["transitions"]) == 0


@pytest.mark.asyncio
async def test_assemble_timeline_with_audio_tracks(client, storyboard_id):
    """Assemble with voiceover and BGM asset IDs."""
    project_id, sb_id = storyboard_id

    resp = await client.post(
        f"/api/v1/projects/{project_id}/timelines/assemble",
        json={
            "storyboard_version_id": sb_id,
            "voiceover_asset_id": 201,
            "bgm_asset_id": 301,
        },
    )

    assert resp.status_code == 200
    tl = resp.json()["data"]
    # 3 tracks: video + voiceover + bgm
    assert len(tl["tracks"]) == 3
    track_types = [t["track_type"] for t in tl["tracks"]]
    assert "video" in track_types
    assert "voiceover" in track_types
    assert "bgm" in track_types

    # BGM volume should be lower
    bgm_track = [t for t in tl["tracks"] if t["track_type"] == "bgm"][0]
    assert bgm_track["clips"][0]["volume"] == 0.3


@pytest.mark.asyncio
async def test_assemble_timeline_with_transitions(client, storyboard_id):
    """Assemble with fade transitions between clips."""
    project_id, sb_id = storyboard_id

    resp = await client.post(
        f"/api/v1/projects/{project_id}/timelines/assemble",
        json={
            "storyboard_version_id": sb_id,
            "default_transition": "fade",
            "transition_duration_ms": 500,
        },
    )

    assert resp.status_code == 200
    tl = resp.json()["data"]
    # 3 clips -> 2 transitions
    assert len(tl["transitions"]) == 2
    assert tl["transitions"][0]["type"] == "fade"
    assert tl["transitions"][0]["duration_ms"] == 500


@pytest.mark.asyncio
async def test_assemble_timeline_nonexistent_project(client):
    """Assemble for non-existent project returns 404."""
    resp = await client.post(
        "/api/v1/projects/99999/timelines/assemble",
        json={"storyboard_version_id": "000000000000000000000000"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_assemble_timeline_nonexistent_storyboard(client, test_project):
    """Assemble with non-existent storyboard returns 404."""
    project_id = test_project["id"]
    resp = await client.post(
        f"/api/v1/projects/{project_id}/timelines/assemble",
        json={"storyboard_version_id": "000000000000000000000000"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_assemble_timeline_invalid_storyboard_id(client, test_project):
    """Assemble with invalid storyboard ID returns 404."""
    project_id = test_project["id"]
    resp = await client.post(
        f"/api/v1/projects/{project_id}/timelines/assemble",
        json={"storyboard_version_id": "invalid-id"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_assemble_timeline_versioning(client, storyboard_id):
    """Assembling twice creates version 1 and 2."""
    project_id, sb_id = storyboard_id

    r1 = await client.post(
        f"/api/v1/projects/{project_id}/timelines/assemble",
        json={"storyboard_version_id": sb_id},
    )
    r2 = await client.post(
        f"/api/v1/projects/{project_id}/timelines/assemble",
        json={"storyboard_version_id": sb_id},
    )

    assert r1.json()["data"]["version_no"] == 1
    assert r2.json()["data"]["version_no"] == 2


# ===== LIST =====


@pytest.mark.asyncio
async def test_list_timelines_empty(client, test_project):
    """List timelines for project with none returns empty."""
    project_id = test_project["id"]
    resp = await client.get(f"/api/v1/projects/{project_id}/timelines")

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_timelines_after_assemble(client, timeline_id):
    """List timelines returns assembled timeline."""
    project_id, _, tl_id = timeline_id
    resp = await client.get(f"/api/v1/projects/{project_id}/timelines")

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["id"] == tl_id


# ===== GET =====


@pytest.mark.asyncio
async def test_get_timeline_success(client, timeline_id):
    """Get a specific timeline by ID."""
    project_id, _, tl_id = timeline_id
    resp = await client.get(f"/api/v1/projects/{project_id}/timelines/{tl_id}")

    assert resp.status_code == 200
    tl = resp.json()["data"]
    assert tl["id"] == tl_id
    assert len(tl["tracks"]) == 1


@pytest.mark.asyncio
async def test_get_timeline_not_found(client, test_project):
    """Get non-existent timeline returns 404."""
    project_id = test_project["id"]
    resp = await client.get(
        f"/api/v1/projects/{project_id}/timelines/000000000000000000000000"
    )
    assert resp.status_code == 404


# ===== UPDATE =====


@pytest.mark.asyncio
async def test_update_timeline_tracks(client, timeline_id):
    """Update timeline tracks."""
    project_id, _, tl_id = timeline_id

    new_tracks = [
        {
            "track_id": "video_main",
            "track_type": "video",
            "clips": [
                {
                    "clip_id": "clip_new_1",
                    "source_shot_id": "shot_001",
                    "source_asset_id": 101,
                    "start_ms": 0,
                    "end_ms": 6000,
                    "offset_ms": 0,
                    "volume": None,
                    "speed": 1.0,
                },
            ],
        },
    ]

    resp = await client.put(
        f"/api/v1/projects/{project_id}/timelines/{tl_id}",
        json={"tracks": new_tracks},
    )

    assert resp.status_code == 200
    tl = resp.json()["data"]
    assert len(tl["tracks"]) == 1
    assert len(tl["tracks"][0]["clips"]) == 1
    assert tl["duration_ms"] == 6000


@pytest.mark.asyncio
async def test_update_timeline_subtitles(client, timeline_id):
    """Update timeline subtitle segments."""
    project_id, _, tl_id = timeline_id

    resp = await client.put(
        f"/api/v1/projects/{project_id}/timelines/{tl_id}",
        json={
            "subtitle_segments": [
                {"id": "sub_new", "start_ms": 0, "end_ms": 3000, "text": "新字幕"},
            ]
        },
    )

    assert resp.status_code == 200
    tl = resp.json()["data"]
    assert len(tl["subtitle_segments"]) == 1
    assert tl["subtitle_segments"][0]["text"] == "新字幕"


@pytest.mark.asyncio
async def test_update_timeline_empty_body(client, timeline_id):
    """Update with empty body returns existing timeline."""
    project_id, _, tl_id = timeline_id
    resp = await client.put(
        f"/api/v1/projects/{project_id}/timelines/{tl_id}",
        json={},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == tl_id


@pytest.mark.asyncio
async def test_update_timeline_not_found(client, test_project):
    """Update non-existent timeline returns 404."""
    project_id = test_project["id"]
    resp = await client.put(
        f"/api/v1/projects/{project_id}/timelines/000000000000000000000000",
        json={"tracks": []},
    )
    assert resp.status_code == 404


# ===== CONFIRM =====


@pytest.mark.asyncio
async def test_confirm_timeline(client, timeline_id):
    """Confirm a timeline version updates the project."""
    project_id, _, tl_id = timeline_id

    resp = await client.post(
        f"/api/v1/projects/{project_id}/timelines/{tl_id}/confirm"
    )

    assert resp.status_code == 200
    tl = resp.json()["data"]
    assert tl["id"] == tl_id

    # Verify project status updated
    proj_resp = await client.get(f"/api/v1/projects/{project_id}")
    proj = proj_resp.json()["data"]
    assert proj["current_timeline_version_id"] is not None
    assert proj["status"] == "timeline_confirmed"


@pytest.mark.asyncio
async def test_confirm_timeline_not_found(client, test_project):
    """Confirm non-existent timeline returns 404."""
    project_id = test_project["id"]
    resp = await client.post(
        f"/api/v1/projects/{project_id}/timelines/000000000000000000000000/confirm"
    )
    assert resp.status_code == 404


# ===== CLIP REORDER =====


@pytest.mark.asyncio
async def test_reorder_clips(client, timeline_id):
    """Reorder clips reverses their positions."""
    project_id, _, tl_id = timeline_id

    # Get current clips
    resp = await client.get(f"/api/v1/projects/{project_id}/timelines/{tl_id}")
    tl = resp.json()["data"]
    clips = tl["tracks"][0]["clips"]
    clip_ids = [c["clip_id"] for c in clips]

    # Reverse the order
    reversed_ids = list(reversed(clip_ids))
    resp = await client.post(
        f"/api/v1/projects/{project_id}/timelines/{tl_id}/clips/reorder",
        json={"track_id": "video_main", "clip_ids": reversed_ids},
    )

    assert resp.status_code == 200
    tl = resp.json()["data"]
    new_clips = tl["tracks"][0]["clips"]
    new_ids = [c["clip_id"] for c in new_clips]
    assert new_ids == reversed_ids

    # Verify timing recalculated: last shot (4s) is now first
    assert new_clips[0]["start_ms"] == 0
    assert new_clips[0]["end_ms"] == 4000  # shot_003 was 4s
    assert new_clips[1]["start_ms"] == 4000
    assert new_clips[1]["end_ms"] == 8000  # shot_002 was 4s


@pytest.mark.asyncio
async def test_reorder_clips_nonexistent_track(client, timeline_id):
    """Reorder clips on non-existent track returns 404."""
    project_id, _, tl_id = timeline_id

    resp = await client.post(
        f"/api/v1/projects/{project_id}/timelines/{tl_id}/clips/reorder",
        json={"track_id": "nonexistent", "clip_ids": ["clip_1"]},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_reorder_clips_nonexistent_clip(client, timeline_id):
    """Reorder with non-existent clip ID returns 404."""
    project_id, _, tl_id = timeline_id

    resp = await client.post(
        f"/api/v1/projects/{project_id}/timelines/{tl_id}/clips/reorder",
        json={"track_id": "video_main", "clip_ids": ["nonexistent_clip"]},
    )
    assert resp.status_code == 404


# ===== CLIP REPLACE =====


@pytest.mark.asyncio
async def test_replace_clip_asset_not_found_asset(client, timeline_id):
    """Replace clip with non-existent asset returns 404."""
    project_id, _, tl_id = timeline_id

    resp = await client.get(f"/api/v1/projects/{project_id}/timelines/{tl_id}")
    clip_id = resp.json()["data"]["tracks"][0]["clips"][0]["clip_id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/timelines/{tl_id}/clips/replace",
        json={
            "track_id": "video_main",
            "clip_id": clip_id,
            "new_asset_id": 99999,
        },
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_replace_clip_not_found_timeline(client, test_project):
    """Replace clip on non-existent timeline returns 404."""
    project_id = test_project["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/timelines/000000000000000000000000/clips/replace",
        json={
            "track_id": "video_main",
            "clip_id": "clip_1",
            "new_asset_id": 1,
        },
    )
    assert resp.status_code == 404
