"""Shot media generation endpoints.

Shots live inside storyboards (MongoDB). This router provides:
  - GET    /{shot_id}                  — Get shot details (from storyboard)
  - PUT    /{shot_id}                  — Update shot prompt/params
  - GET    /{shot_id}/assets           — List assets for a shot
  - POST   /{shot_id}/images/generate  — Generate keyframe image(s)
  - POST   /{shot_id}/videos/generate  — Generate video from prompt or image
  - GET    /{shot_id}/tasks/{task_id}  — Get generation task status

Image generation uses GPTImageGateway (sync in MVP, async later).
Video generation uses KlingVideoGateway (submit + poll).
Generated files are stored in MinIO; references tracked in AssetFile + GenerationTask tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.common.database import get_db
from packages.common.exceptions import NotFoundError
from packages.common.mongo import Collections, get_mongo_db
from packages.common.response import ApiResponse, PagedData
from packages.common.storage import build_object_key, get_presigned_url, upload_bytes
from packages.domain.models import AssetFile, GenerationTask
from packages.model_gateways.image_gateway import GPTImageGateway
from packages.model_gateways.video_gateway import KlingVideoGateway, VideoInputMode
from services.api_service.app.schemas.api_schemas import (
    AssetOut,
    GenerateImageRequest,
    GenerateVideoRequest,
    GenerationTaskOut,
    ShotOut,
    ShotUpdate,
)

router = APIRouter(prefix="/projects/{project_id}/shots", tags=["shots"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _find_shot_in_storyboard(
    project_id: int, shot_id: str
) -> tuple[dict, dict, str]:
    """Find a shot within the latest storyboard for a project.

    Returns (storyboard_doc, shot_spec_dict, scene_id).
    Raises NotFoundError if not found.
    """
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.STORYBOARD]

    # Find the latest storyboard for this project
    cursor = coll.find({"project_id": project_id}).sort("version_no", -1).limit(1)
    docs = await cursor.to_list(length=1)
    if not docs:
        raise NotFoundError("Storyboard for project", project_id)

    sb_doc = docs[0]
    for scene in sb_doc.get("scenes", []):
        for shot in scene.get("shots", []):
            if shot.get("shot_id") == shot_id:
                return sb_doc, shot, scene.get("scene_id", "")

    raise NotFoundError("Shot", shot_id)


def _shot_to_out(shot: dict, scene_id: str) -> ShotOut:
    """Convert a shot spec dict to ShotOut."""
    return ShotOut(
        shot_id=shot.get("shot_id", ""),
        scene_id=scene_id,
        order_no=shot.get("order_no", 0),
        shot_type=shot.get("shot_type", "wide"),
        camera_movement=shot.get("camera_movement", "static"),
        character_desc=shot.get("character_desc", ""),
        environment_desc=shot.get("environment_desc", ""),
        action_desc=shot.get("action_desc", ""),
        voiceover_text=shot.get("voiceover_text", ""),
        image_prompt=shot.get("image_prompt", ""),
        video_prompt=shot.get("video_prompt", ""),
        duration_sec=shot.get("duration_sec", 4.0),
        status=shot.get("status", "pending"),
        selected_asset_ids=shot.get("selected_asset_ids", []),
    )


def _asset_to_out(asset: AssetFile, presigned: str | None = None) -> AssetOut:
    """Convert an AssetFile ORM instance to AssetOut."""
    out = AssetOut.model_validate(asset)
    out.presigned_url = presigned
    return out


async def _update_shot_status(
    project_id: int, shot_id: str, new_status: str
) -> None:
    """Update a shot's status in the storyboard MongoDB document."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.STORYBOARD]

    cursor = coll.find({"project_id": project_id}).sort("version_no", -1).limit(1)
    docs = await cursor.to_list(length=1)
    if not docs:
        return

    sb_doc = docs[0]
    updated = False
    for scene in sb_doc.get("scenes", []):
        for shot in scene.get("shots", []):
            if shot.get("shot_id") == shot_id:
                shot["status"] = new_status
                updated = True
                break
        if updated:
            break

    if updated:
        await coll.update_one(
            {"_id": sb_doc["_id"]},
            {"$set": {"scenes": sb_doc["scenes"]}},
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/{shot_id}", response_model=ApiResponse[ShotOut])
async def get_shot(project_id: int, shot_id: str) -> ApiResponse[ShotOut]:
    """Get a specific shot's details from the storyboard."""
    _, shot, scene_id = await _find_shot_in_storyboard(project_id, shot_id)
    return ApiResponse(data=_shot_to_out(shot, scene_id))


@router.put("/{shot_id}", response_model=ApiResponse[ShotOut])
async def update_shot(
    project_id: int,
    shot_id: str,
    body: ShotUpdate,
) -> ApiResponse[ShotOut]:
    """Update a shot's editable fields (prompts, descriptions, etc.)."""
    sb_doc, shot, scene_id = await _find_shot_in_storyboard(project_id, shot_id)

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        return ApiResponse(data=_shot_to_out(shot, scene_id))

    # Apply updates to the shot dict
    for key, value in update_data.items():
        shot[key] = value

    # Write back to MongoDB
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.STORYBOARD]
    await coll.update_one(
        {"_id": sb_doc["_id"]},
        {"$set": {"scenes": sb_doc["scenes"]}},
    )

    return ApiResponse(data=_shot_to_out(shot, scene_id))


@router.get("/{shot_id}/assets", response_model=ApiResponse[PagedData[AssetOut]])
async def get_shot_assets(
    project_id: int,
    shot_id: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PagedData[AssetOut]]:
    """List all generated assets for a shot."""
    # biz_key pattern: "shot:{shot_id}"
    biz_key = f"shot:{shot_id}"

    # Find assets through their generation tasks
    task_stmt = (
        select(GenerationTask.id)
        .where(
            GenerationTask.project_id == project_id,
            GenerationTask.biz_key == biz_key,
        )
    )
    task_result = await db.execute(task_stmt)
    task_ids = [row[0] for row in task_result.all()]

    if not task_ids:
        return ApiResponse(
            data=PagedData(items=[], total=0, page=page, page_size=page_size)
        )

    # Get asset IDs from generation tasks output_ref
    asset_stmt = (
        select(AssetFile)
        .where(
            AssetFile.project_id == project_id,
            AssetFile.status == "active",
        )
        .order_by(AssetFile.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    # Filter by biz_key pattern in object_key
    # Object keys contain the shot_id: projects/{pid}/shots/{shot_id}/...
    result = await db.execute(asset_stmt)
    assets = list(result.scalars().all())

    # Filter to only assets belonging to this shot (by object_key pattern)
    shot_assets = [
        a for a in assets if f"/shots/{shot_id}/" in (a.object_key or "")
    ]

    items = []
    for asset in shot_assets:
        try:
            url = get_presigned_url(asset.object_key)
        except Exception:
            url = None
        items.append(_asset_to_out(asset, url))

    return ApiResponse(
        data=PagedData(items=items, total=len(items), page=page, page_size=page_size)
    )


@router.post("/{shot_id}/images/generate", response_model=ApiResponse[GenerationTaskOut])
async def generate_keyframe(
    project_id: int,
    shot_id: str,
    body: GenerateImageRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[GenerationTaskOut]:
    """Generate keyframe image(s) for a shot.

    Flow:
      1. Validate shot exists in storyboard
      2. Create GenerationTask record (status=processing)
      3. Call GPTImageGateway to generate image(s)
      4. Upload each image to MinIO
      5. Create AssetFile records
      6. Update GenerationTask with output_ref + status=completed
      7. Update shot status to image_ready
    """
    # 1. Validate shot exists
    _, shot, scene_id = await _find_shot_in_storyboard(project_id, shot_id)

    # Determine the prompt
    prompt = body.prompt_override or shot.get("image_prompt", "")
    if not prompt:
        prompt = f"{shot.get('environment_desc', '')} {shot.get('character_desc', '')} {shot.get('action_desc', '')}"

    # 2. Create generation task
    biz_key = f"shot:{shot_id}"
    gen_task = GenerationTask(
        tenant_id=1,
        project_id=project_id,
        task_type="image_generation",
        biz_key=biz_key,
        model_provider="openai",
        model_name=body.image_model,
        input_ref={
            "shot_id": shot_id,
            "prompt": prompt,
            "resolution": body.resolution,
            "candidate_count": body.candidate_count,
            "reference_asset_ids": body.reference_asset_ids,
        },
        status="processing",
    )
    db.add(gen_task)
    await db.flush()
    await db.refresh(gen_task)

    # 3. Update shot status to image_generating
    await _update_shot_status(project_id, shot_id, "image_generating")

    try:
        # 4. Call image gateway
        gateway = GPTImageGateway()
        images = await gateway.generate(
            prompt=prompt,
            n=body.candidate_count,
            size=body.resolution,
        )

        # 5. Upload to MinIO + create AssetFile records
        asset_ids = []
        for idx, img_bytes in enumerate(images):
            filename = f"keyframe_{uuid.uuid4().hex[:8]}.png"
            object_key = build_object_key(project_id, shot_id, "keyframe", filename)

            upload_bytes(object_key, img_bytes, content_type="image/png")

            asset = AssetFile(
                tenant_id=1,
                project_id=project_id,
                asset_type="image",
                usage_type="keyframe",
                mime_type="image/png",
                file_name=filename,
                object_key=object_key,
                file_size=len(img_bytes),
                status="active",
            )
            db.add(asset)
            await db.flush()
            await db.refresh(asset)
            asset_ids.append(asset.id)

        # 6. Update task to completed
        gen_task.status = "completed"
        gen_task.output_ref = {"asset_ids": asset_ids}
        await db.flush()
        await db.refresh(gen_task)

        # 7. Update shot status
        await _update_shot_status(project_id, shot_id, "image_ready")

    except Exception as e:
        # Mark task as failed
        gen_task.status = "failed"
        gen_task.error_message = str(e)
        await db.flush()
        await db.refresh(gen_task)

        await _update_shot_status(project_id, shot_id, "failed")

    return ApiResponse(data=GenerationTaskOut.model_validate(gen_task))


@router.post("/{shot_id}/videos/generate", response_model=ApiResponse[GenerationTaskOut])
async def generate_video(
    project_id: int,
    shot_id: str,
    body: GenerateVideoRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[GenerationTaskOut]:
    """Generate video for a shot.

    Supports two modes:
      - text_to_video: Generate directly from prompt
      - image_to_video: Generate from a keyframe image (requires image_asset_id)

    Flow:
      1. Validate shot exists
      2. If image_to_video, get the image asset's presigned URL
      3. Create GenerationTask record (status=processing)
      4. Submit task to KlingVideoGateway (returns external task_id)
      5. Poll for completion (MVP: synchronous polling, later: webhook/async)
      6. Download video + upload to MinIO
      7. Create AssetFile record
      8. Update GenerationTask + shot status
    """
    # 1. Validate shot
    _, shot, scene_id = await _find_shot_in_storyboard(project_id, shot_id)

    prompt = body.prompt_override or shot.get("video_prompt", "")
    if not prompt:
        prompt = f"{shot.get('action_desc', '')} {shot.get('environment_desc', '')}"

    # 2. Resolve image URL for image_to_video mode
    image_url: str | None = None
    if body.input_mode == "image_to_video":
        if body.image_asset_id is None:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=422,
                detail="image_asset_id is required for image_to_video mode",
            )
        # Look up the asset
        stmt = select(AssetFile).where(
            AssetFile.id == body.image_asset_id,
            AssetFile.project_id == project_id,
        )
        result = await db.execute(stmt)
        image_asset = result.scalar_one_or_none()
        if image_asset is None:
            raise NotFoundError("AssetFile", body.image_asset_id)

        image_url = get_presigned_url(image_asset.object_key)

    # 3. Create generation task
    biz_key = f"shot:{shot_id}"
    input_mode_enum = VideoInputMode(body.input_mode)
    gen_task = GenerationTask(
        tenant_id=1,
        project_id=project_id,
        task_type="video_generation",
        biz_key=biz_key,
        model_provider="kling",
        model_name=body.video_model,
        input_ref={
            "shot_id": shot_id,
            "prompt": prompt,
            "input_mode": body.input_mode,
            "image_asset_id": body.image_asset_id,
            "duration_sec": body.duration_sec,
            "resolution": body.resolution,
        },
        status="processing",
    )
    db.add(gen_task)
    await db.flush()
    await db.refresh(gen_task)

    # 4. Update shot status
    await _update_shot_status(project_id, shot_id, "video_generating")

    try:
        # 5. Submit to Kling
        gateway = KlingVideoGateway()
        external_task_id = await gateway.submit_task(
            prompt=prompt,
            mode=input_mode_enum,
            image_url=image_url,
            duration_sec=body.duration_sec,
            model_name=body.video_model,
        )

        # 6. Poll for completion (MVP: simple polling loop)
        import asyncio

        max_polls = 120  # 10 minutes with 5s interval
        video_url: str | None = None

        for _ in range(max_polls):
            await asyncio.sleep(5)
            result = await gateway.query_task(external_task_id)

            if result.status == "succeed":
                video_url = result.video_url
                break
            elif result.status == "failed":
                raise RuntimeError(
                    f"Kling task {external_task_id} failed: {result.error_message}"
                )
            # else: still processing, continue polling

        if video_url is None:
            raise TimeoutError(
                f"Kling task {external_task_id} did not complete within timeout"
            )

        # 7. Download video + upload to MinIO
        video_bytes = await gateway.download_video(video_url)
        filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
        object_key = build_object_key(project_id, shot_id, "video", filename)
        upload_bytes(object_key, video_bytes, content_type="video/mp4")

        # 8. Create AssetFile
        asset = AssetFile(
            tenant_id=1,
            project_id=project_id,
            asset_type="video",
            usage_type="shot_video",
            mime_type="video/mp4",
            file_name=filename,
            object_key=object_key,
            file_size=len(video_bytes),
            duration_ms=int(body.duration_sec * 1000),
            status="active",
        )
        db.add(asset)
        await db.flush()
        await db.refresh(asset)

        # 9. Update task
        gen_task.status = "completed"
        gen_task.output_ref = {
            "asset_id": asset.id,
            "external_task_id": external_task_id,
        }
        await db.flush()
        await db.refresh(gen_task)

        # 10. Update shot status
        await _update_shot_status(project_id, shot_id, "video_ready")

    except Exception as e:
        gen_task.status = "failed"
        gen_task.error_message = str(e)
        await db.flush()
        await db.refresh(gen_task)

        await _update_shot_status(project_id, shot_id, "failed")

    return ApiResponse(data=GenerationTaskOut.model_validate(gen_task))


@router.get(
    "/{shot_id}/tasks/{task_id}",
    response_model=ApiResponse[GenerationTaskOut],
)
async def get_generation_task(
    project_id: int,
    shot_id: str,
    task_id: int,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[GenerationTaskOut]:
    """Get the status of a specific generation task."""
    stmt = select(GenerationTask).where(
        GenerationTask.id == task_id,
        GenerationTask.project_id == project_id,
        GenerationTask.biz_key == f"shot:{shot_id}",
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if task is None:
        raise NotFoundError("GenerationTask", task_id)

    return ApiResponse(data=GenerationTaskOut.model_validate(task))


@router.delete("/{shot_id}")
async def delete_shot(project_id: int, shot_id: str) -> ApiResponse:
    """Delete a shot from the storyboard (removes from scenes array)."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.STORYBOARD]

    cursor = coll.find({"project_id": project_id}).sort("version_no", -1).limit(1)
    docs = await cursor.to_list(length=1)
    if not docs:
        raise NotFoundError("Storyboard for project", project_id)

    sb_doc = docs[0]
    found = False
    for scene in sb_doc.get("scenes", []):
        original_len = len(scene.get("shots", []))
        scene["shots"] = [
            s for s in scene.get("shots", []) if s.get("shot_id") != shot_id
        ]
        if len(scene["shots"]) < original_len:
            found = True
            break

    if not found:
        raise NotFoundError("Shot", shot_id)

    await coll.update_one(
        {"_id": sb_doc["_id"]},
        {"$set": {"scenes": sb_doc["scenes"]}},
    )

    return ApiResponse(message="deleted")
