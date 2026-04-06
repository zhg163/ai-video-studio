"""E2E full pipeline integration test — 创意输入到 Storyboard 确认.

覆盖完整创作链路（不 mock LLM，真实调用 Qwen API）：
  1. 创建项目
  2. 生成 Brief（真实 LLM）→ 确认 Brief
  3. 生成 Script（真实 LLM）→ 确认 Script
  4. 生成 Storyboard（真实 LLM）→ 确认 Storyboard
  5. Smoke Test：全链路一次性跑通

说明：
  - confirm 端点返回完整文档对象（BriefOut/ScriptOut/StoryboardOut），无 status 字段
  - status 字段在 ProjectOut 上，通过 GET /projects/{id} 验证
  - 标记为 @pytest.mark.e2e，默认跳过，需 -m e2e 才运行

运行命令：
  pytest -m e2e services/api_service/tests/test_e2e_pipeline.py -v
"""

from __future__ import annotations

import asyncio

import pytest

from packages.common.mongo import Collections, get_mongo_db


pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
async def cleanup_all():
    """每个测试结束后清空所有 MongoDB 集合。"""
    yield
    try:
        db = get_mongo_db()
        for col in [
            Collections.CREATIVE_BRIEF,
            Collections.SCRIPT,
            Collections.STORYBOARD,
            Collections.TIMELINE,
        ]:
            await db[col].delete_many({})
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Helper: 带重试的 POST（网络抖动时自动重试）
# ---------------------------------------------------------------------------


async def post_with_retry(client, url, json_body, *, retries=2, delay=2):
    """POST with simple retry on 500 (network/proxy transient errors)."""
    last_resp = None
    for attempt in range(retries + 1):
        resp = await client.post(url, json=json_body)
        if resp.status_code != 500:
            return resp
        last_resp = resp
        if attempt < retries:
            await asyncio.sleep(delay)
    return last_resp


# ---------------------------------------------------------------------------
# Stage 1: 创建项目
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_create_project(client):
    """E2E Stage 1: 创建项目，验证返回结构。"""
    resp = await client.post(
        "/api/v1/projects",
        json={"name": "春天短视频 E2E", "description": "E2E 全链路测试项目"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    project = data["data"]
    assert project["id"] > 0
    assert project["name"] == "春天短视频 E2E"
    assert project["status"] == "draft"


# ---------------------------------------------------------------------------
# Stage 2: 生成 Brief（真实 LLM）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_generate_brief(client, test_project):
    """E2E Stage 2a: 真实 LLM 生成 Brief，验证结构化字段完整。"""
    pid = test_project["id"]

    resp = await post_with_retry(
        client,
        f"/api/v1/projects/{pid}/briefs/generate",
        {"text": "做一个关于春天的30秒短视频，展示花朵盛开、阳光明媚的场景，风格温馨治愈，发布在抖音。"},
    )
    assert resp.status_code == 200, f"Brief generate failed: {resp.text}"
    data = resp.json()
    assert data["code"] == 0, f"Unexpected code: {data}"
    brief = data["data"]

    assert brief["project_id"] == pid
    assert brief["version_no"] == 1
    assert "id" in brief

    sb = brief["structured_brief"]
    assert sb["goal"], "goal 不能为空"
    assert sb["audience"], "audience 不能为空"
    assert isinstance(sb["duration_sec"], int) and sb["duration_sec"] > 0
    assert sb["aspect_ratio"] in ("16:9", "9:16", "1:1", "4:3")
    assert sb["language"]
    assert sb["style"]
    assert sb["platform"]

    constraints = brief["constraints"]
    assert isinstance(constraints["must_include"], list)
    assert len(constraints["must_include"]) >= 1
    assert isinstance(constraints["must_not"], list)
    assert constraints["max_duration_sec"] > 0

    src = brief["source_input"]
    assert "春天" in src["text"]


@pytest.mark.asyncio
async def test_e2e_confirm_brief(client, test_project):
    """E2E Stage 2b: 生成 Brief 后确认，项目状态变为 brief_confirmed。

    confirm 端点返回 BriefOut（无 status 字段）。
    项目状态通过 GET /projects/{id} 单独验证。
    """
    pid = test_project["id"]

    # 生成
    gen_resp = await post_with_retry(
        client,
        f"/api/v1/projects/{pid}/briefs/generate",
        {"text": "春天花朵短视频，30秒，抖音平台。"},
    )
    assert gen_resp.status_code == 200
    brief_id = gen_resp.json()["data"]["id"]

    # 确认 — 返回 BriefOut，验证 id 和 project_id 正确
    confirm_resp = await client.post(f"/api/v1/projects/{pid}/briefs/{brief_id}/confirm")
    assert confirm_resp.status_code == 200, f"Brief confirm failed: {confirm_resp.text}"
    data = confirm_resp.json()
    assert data["code"] == 0
    assert data["data"]["id"] == brief_id
    assert data["data"]["project_id"] == pid

    # 验证项目状态已更新
    proj_resp = await client.get(f"/api/v1/projects/{pid}")
    assert proj_resp.json()["data"]["status"] == "brief_confirmed"


# ---------------------------------------------------------------------------
# Stage 3: 生成 Script（真实 LLM）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_generate_script(client, test_project):
    """E2E Stage 3a: 基于 Brief 真实 LLM 生成 Script，验证章节结构。"""
    pid = test_project["id"]

    gen_resp = await post_with_retry(
        client,
        f"/api/v1/projects/{pid}/briefs/generate",
        {"text": "春天花朵短视频，30秒，温馨风格，抖音平台。"},
    )
    assert gen_resp.status_code == 200
    brief_id = gen_resp.json()["data"]["id"]
    await client.post(f"/api/v1/projects/{pid}/briefs/{brief_id}/confirm")

    script_resp = await post_with_retry(
        client,
        f"/api/v1/projects/{pid}/scripts/generate",
        {"brief_version_id": brief_id},
    )
    assert script_resp.status_code == 200, f"Script generate failed: {script_resp.text}"
    data = script_resp.json()
    assert data["code"] == 0
    script = data["data"]

    assert script["project_id"] == pid
    assert script["version_no"] == 1
    assert "id" in script
    assert script["title"], "title 不能为空"
    assert script["language"]
    assert isinstance(script["sections"], list)
    assert len(script["sections"]) >= 1

    for sec in script["sections"]:
        assert isinstance(sec["section_no"], int)
        assert sec["title"]
        assert sec["narration"], f"section {sec['section_no']} narration 不能为空"

    assert script["full_text"], "full_text 不能为空"


@pytest.mark.asyncio
async def test_e2e_confirm_script(client, test_project):
    """E2E Stage 3b: 生成 Script 后确认，项目状态变为 script_confirmed。

    confirm 端点返回 ScriptOut（无 status 字段）。
    """
    pid = test_project["id"]

    gen_resp = await post_with_retry(
        client,
        f"/api/v1/projects/{pid}/briefs/generate",
        {"text": "春天花朵短视频，30秒，抖音。"},
    )
    brief_id = gen_resp.json()["data"]["id"]
    await client.post(f"/api/v1/projects/{pid}/briefs/{brief_id}/confirm")

    script_resp = await post_with_retry(
        client,
        f"/api/v1/projects/{pid}/scripts/generate",
        {"brief_version_id": brief_id},
    )
    assert script_resp.status_code == 200
    script_id = script_resp.json()["data"]["id"]

    # 确认 — 返回 ScriptOut
    confirm_resp = await client.post(f"/api/v1/projects/{pid}/scripts/{script_id}/confirm")
    assert confirm_resp.status_code == 200, f"Script confirm failed: {confirm_resp.text}"
    data = confirm_resp.json()
    assert data["code"] == 0
    assert data["data"]["id"] == script_id
    assert data["data"]["project_id"] == pid

    # 项目状态
    proj_resp = await client.get(f"/api/v1/projects/{pid}")
    assert proj_resp.json()["data"]["status"] == "script_confirmed"


# ---------------------------------------------------------------------------
# Stage 4: 生成 Storyboard（真实 LLM）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_generate_storyboard(client, test_project):
    """E2E Stage 4a: 基于 Script 真实 LLM 生成 Storyboard，验证场景/镜头结构。"""
    pid = test_project["id"]

    gen_resp = await post_with_retry(
        client,
        f"/api/v1/projects/{pid}/briefs/generate",
        {"text": "春天花朵短视频，30秒，温馨治愈风格，抖音平台。"},
    )
    brief_id = gen_resp.json()["data"]["id"]
    await client.post(f"/api/v1/projects/{pid}/briefs/{brief_id}/confirm")

    script_resp = await post_with_retry(
        client,
        f"/api/v1/projects/{pid}/scripts/generate",
        {"brief_version_id": brief_id},
    )
    script_id = script_resp.json()["data"]["id"]
    await client.post(f"/api/v1/projects/{pid}/scripts/{script_id}/confirm")

    sb_resp = await post_with_retry(
        client,
        f"/api/v1/projects/{pid}/storyboards/generate",
        {"script_version_id": script_id},
    )
    assert sb_resp.status_code == 200, f"Storyboard generate failed: {sb_resp.text}"
    data = sb_resp.json()
    assert data["code"] == 0
    sb = data["data"]

    assert sb["project_id"] == pid
    assert sb["version_no"] == 1
    assert "id" in sb

    scenes = sb["scenes"]
    assert isinstance(scenes, list)
    assert len(scenes) >= 1, "至少要有 1 个场景"

    total_shots = 0
    for scene in scenes:
        assert scene["scene_id"], "scene_id 不能为空"
        assert scene["title"], "scene title 不能为空"
        assert isinstance(scene["shots"], list)
        assert len(scene["shots"]) >= 1, f"场景 {scene['scene_id']} 至少要有 1 个镜头"
        total_shots += len(scene["shots"])

        for shot in scene["shots"]:
            assert shot["shot_id"], "shot_id 不能为空"
            assert isinstance(shot["order_no"], int)
            assert shot["shot_type"]
            assert shot["image_prompt"], f"shot {shot['shot_id']} image_prompt 不能为空"
            assert shot["video_prompt"], f"shot {shot['shot_id']} video_prompt 不能为空"
            assert shot["duration_sec"] > 0
            assert shot["status"] == "pending"

    assert total_shots >= 2, f"总镜头数应 >= 2，实际: {total_shots}"


@pytest.mark.asyncio
async def test_e2e_confirm_storyboard(client, test_project):
    """E2E Stage 4b: 生成 Storyboard 后确认，项目状态变为 storyboard_confirmed。

    confirm 端点返回 StoryboardOut（无 status 字段）。
    """
    pid = test_project["id"]

    gen_resp = await post_with_retry(
        client,
        f"/api/v1/projects/{pid}/briefs/generate",
        {"text": "春天30秒短视频，抖音平台。"},
    )
    brief_id = gen_resp.json()["data"]["id"]
    await client.post(f"/api/v1/projects/{pid}/briefs/{brief_id}/confirm")

    script_resp = await post_with_retry(
        client,
        f"/api/v1/projects/{pid}/scripts/generate",
        {"brief_version_id": brief_id},
    )
    script_id = script_resp.json()["data"]["id"]
    await client.post(f"/api/v1/projects/{pid}/scripts/{script_id}/confirm")

    sb_resp = await post_with_retry(
        client,
        f"/api/v1/projects/{pid}/storyboards/generate",
        {"script_version_id": script_id},
    )
    assert sb_resp.status_code == 200
    sb_id = sb_resp.json()["data"]["id"]

    # 确认 — 返回 StoryboardOut
    confirm_resp = await client.post(
        f"/api/v1/projects/{pid}/storyboards/{sb_id}/confirm"
    )
    assert confirm_resp.status_code == 200, f"Storyboard confirm failed: {confirm_resp.text}"
    data = confirm_resp.json()
    assert data["code"] == 0
    assert data["data"]["id"] == sb_id
    assert data["data"]["project_id"] == pid

    # 项目状态
    proj_resp = await client.get(f"/api/v1/projects/{pid}")
    assert proj_resp.json()["data"]["status"] == "storyboard_confirmed"


# ---------------------------------------------------------------------------
# Full pipeline smoke test: Project → Brief → Script → Storyboard (一次性)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_full_pipeline_smoke(client, test_project):
    """E2E Smoke Test: 一次性跑完 Project→Brief→Script→Storyboard 全链路。

    验证：
    - 各阶段 HTTP 200 且 code==0
    - ID 正确传递（brief_id → script, script_id → storyboard）
    - 最终 Storyboard 有效：包含场景、镜头、image_prompt
    - 项目最终状态为 storyboard_confirmed
    """
    pid = test_project["id"]

    # ── Step 1: 生成 Brief ────────────────────────────────────────────────
    r = await post_with_retry(
        client,
        f"/api/v1/projects/{pid}/briefs/generate",
        {"text": "春天花朵短视频30秒，温馨风格，抖音平台。"},
    )
    assert r.status_code == 200, f"[Brief generate] {r.text}"
    brief = r.json()["data"]
    brief_id = brief["id"]
    assert brief["structured_brief"]["goal"]
    assert brief["structured_brief"]["style"]

    # ── Step 2: 确认 Brief ───────────────────────────────────────────────
    r = await client.post(f"/api/v1/projects/{pid}/briefs/{brief_id}/confirm")
    assert r.status_code == 200, f"[Brief confirm] {r.text}"
    assert r.json()["data"]["id"] == brief_id  # BriefOut，无 status 字段

    # ── Step 3: 生成 Script ──────────────────────────────────────────────
    r = await post_with_retry(
        client,
        f"/api/v1/projects/{pid}/scripts/generate",
        {"brief_version_id": brief_id},
    )
    assert r.status_code == 200, f"[Script generate] {r.text}"
    script = r.json()["data"]
    script_id = script["id"]
    assert len(script["sections"]) >= 1
    assert script["full_text"]

    # ── Step 4: 确认 Script ──────────────────────────────────────────────
    r = await client.post(f"/api/v1/projects/{pid}/scripts/{script_id}/confirm")
    assert r.status_code == 200, f"[Script confirm] {r.text}"
    assert r.json()["data"]["id"] == script_id  # ScriptOut，无 status 字段

    # ── Step 5: 生成 Storyboard ──────────────────────────────────────────
    r = await post_with_retry(
        client,
        f"/api/v1/projects/{pid}/storyboards/generate",
        {"script_version_id": script_id},
    )
    assert r.status_code == 200, f"[Storyboard generate] {r.text}"
    sb = r.json()["data"]
    sb_id = sb["id"]

    scenes = sb["scenes"]
    assert len(scenes) >= 1
    all_shots = [s for scene in scenes for s in scene["shots"]]
    assert len(all_shots) >= 2

    for shot in all_shots:
        assert shot["image_prompt"], f"shot {shot['shot_id']} 缺少 image_prompt"
        assert shot["video_prompt"], f"shot {shot['shot_id']} 缺少 video_prompt"

    # ── Step 6: 确认 Storyboard ──────────────────────────────────────────
    r = await client.post(f"/api/v1/projects/{pid}/storyboards/{sb_id}/confirm")
    assert r.status_code == 200, f"[Storyboard confirm] {r.text}"
    assert r.json()["data"]["id"] == sb_id  # StoryboardOut，无 status 字段

    # ── 最终验证：项目状态 ────────────────────────────────────────────────
    r = await client.get(f"/api/v1/projects/{pid}")
    assert r.status_code == 200
    final_status = r.json()["data"]["status"]
    assert final_status == "storyboard_confirmed", (
        f"期望 storyboard_confirmed，实际 {final_status}"
    )
