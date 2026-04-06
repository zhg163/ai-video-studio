"""Audio / TTS / voiceover endpoints.

Endpoints:
  - POST /projects/{project_id}/audio/generate-voiceover
      Batch-generate voiceover for all shots in a storyboard version.
  - POST /projects/{project_id}/shots/{shot_id}/audios/generate
      Generate voiceover for a single shot.
  - GET  /projects/{project_id}/audio/voiceovers
      List all voiceover assets for a project.
"""

from __future__ import annotations

import logging
import uuid

from bson import ObjectId
from fastapi import APIRouter, Depends
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from packages.common.database import get_db
from packages.common.exceptions import NotFoundError
from packages.common.mongo import Collections, get_mongo_db
from packages.common.response import ApiResponse, PagedData
from packages.common.storage import build_object_key, get_presigned_url, upload_bytes
from packages.domain.models import AssetFile, GenerationTask
from packages.model_gateways.audio_gateway import QwenTTSGateway
from services.api_service.app.schemas.api_schemas import (
    AssetOut,
    BatchVoiceoverOut,
    GenerateVoiceoverForShotRequest,
    GenerateVoiceoverRequest,
    GenerationTaskOut,
    VoiceoverResultItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["audio"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_storyboard_by_id(storyboard_version_id: str) -> dict:
    """Look up a storyboard document by its MongoDB _id."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.STORYBOARD]
    doc = await coll.find_one({"_id": ObjectId(storyboard_version_id)})
    if not doc:
        raise NotFoundError("Storyboard", storyboard_version_id)
    return doc


async def _get_latest_storyboard(project_id: int) -> dict:
    """Get the latest storyboard for a project."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.STORYBOARD]
    cursor = coll.find({"project_id": project_id}).sort("version_no", -1).limit(1)
    docs = await cursor.to_list(length=1)
    if not docs:
        raise NotFoundError("Storyboard for project", project_id)
    return docs[0]


def _collect_shots(storyboard_doc: dict) -> list[dict]:
    """Flatten all shots from all scenes in a storyboard."""
    shots = []
    for scene in storyboard_doc.get("scenes", []):
        for shot in scene.get("shots", []):
            shots.append(shot)
    return shots


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


async def _synthesize_shot_voiceover(
    project_id: int,
    shot_id: str,
    text: str,
    voice_name: str,
    speed: float,
    db: AsyncSession,
) -> tuple[int | None, str, str | None]:
    """Synthesize TTS for one shot text, upload to MinIO, create records.

    Returns (asset_id, status, error_message).
    """
    if not text or not text.strip():
        return None, "skipped", None

    # Create GenerationTask
    biz_key = f"shot:{shot_id}"
    gen_task = GenerationTask(
        tenant_id=1,
        project_id=project_id,
        task_type="voiceover_generate",
        biz_key=biz_key,
        model_provider="qwen",
        model_name="qwen3-tts",
        input_ref={
            "shot_id": shot_id,
            "text": text,
            "voice": voice_name,
            "speed": speed,
        },
        status="processing",
    )
    db.add(gen_task)
    await db.flush()
    await db.refresh(gen_task)

    # Update shot status
    await _update_shot_status(project_id, shot_id, "audio_generating")

    try:
        # Call TTS gateway
        gateway = QwenTTSGateway()
        audio_bytes = await gateway.synthesize(
            text=text,
            voice=voice_name,
            speed=speed,
        )

        # Upload to MinIO
        filename = f"voiceover_{uuid.uuid4().hex[:8]}.mp3"
        object_key = build_object_key(project_id, shot_id, "voiceover", filename)
        upload_bytes(object_key, audio_bytes, content_type="audio/mpeg")

        # Create AssetFile
        asset = AssetFile(
            tenant_id=1,
            project_id=project_id,
            asset_type="audio",
            usage_type="tts",
            mime_type="audio/mpeg",
            file_name=filename,
            object_key=object_key,
            file_size=len(audio_bytes),
            status="active",
        )
        db.add(asset)
        await db.flush()
        await db.refresh(asset)

        # Update task
        gen_task.status = "completed"
        gen_task.output_ref = {"asset_id": asset.id}
        await db.flush()

        # Update shot status
        await _update_shot_status(project_id, shot_id, "ready")

        return asset.id, "completed", None

    except Exception as e:
        logger.error("TTS synthesis failed for shot %s: %s", shot_id, e)
        gen_task.status = "failed"
        gen_task.error_message = str(e)
        await db.flush()

        await _update_shot_status(project_id, shot_id, "failed")

        return None, "failed", str(e)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/projects/{project_id}/audio/generate-voiceover",
    response_model=ApiResponse[BatchVoiceoverOut],
)
async def generate_voiceover_batch(
    project_id: int,
    body: GenerateVoiceoverRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[BatchVoiceoverOut]:
    """Batch-generate voiceover for all shots in a storyboard.

    Iterates over all shots in the specified storyboard version, calls
    QwenTTSGateway for each shot with voiceover_text, uploads audio to
    MinIO, and creates AssetFile + GenerationTask records.
    """
    # Look up storyboard
    sb_doc = await _get_storyboard_by_id(body.storyboard_version_id)

    # Validate project ownership
    if sb_doc.get("project_id") != project_id:
        raise NotFoundError("Storyboard for project", project_id)

    shots = _collect_shots(sb_doc)
    results: list[VoiceoverResultItem] = []
    completed = 0
    failed = 0
    skipped = 0

    for shot in shots:
        shot_id = shot.get("shot_id", "")
        text = shot.get("voiceover_text", "")

        asset_id, status, error = await _synthesize_shot_voiceover(
            project_id=project_id,
            shot_id=shot_id,
            text=text,
            voice_name=body.voice_name,
            speed=body.speed,
            db=db,
        )

        results.append(VoiceoverResultItem(
            shot_id=shot_id,
            asset_id=asset_id,
            status=status,
            error=error,
        ))

        if status == "completed":
            completed += 1
        elif status == "failed":
            failed += 1
        else:
            skipped += 1

    out = BatchVoiceoverOut(
        project_id=project_id,
        storyboard_version_id=body.storyboard_version_id,
        results=results,
        total=len(results),
        completed=completed,
        failed=failed,
        skipped=skipped,
    )
    return ApiResponse(data=out)


@router.post(
    "/projects/{project_id}/shots/{shot_id}/audios/generate",
    response_model=ApiResponse[GenerationTaskOut],
)
async def generate_voiceover_for_shot(
    project_id: int,
    shot_id: str,
    body: GenerateVoiceoverForShotRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[GenerationTaskOut]:
    """Generate voiceover audio for a single shot.

    Uses the shot's voiceover_text (or text_override) to synthesize speech.
    """
    # Validate shot exists
    sb_doc = await _get_latest_storyboard(project_id)
    shot_found = None
    for scene in sb_doc.get("scenes", []):
        for shot in scene.get("shots", []):
            if shot.get("shot_id") == shot_id:
                shot_found = shot
                break
        if shot_found:
            break

    if shot_found is None:
        raise NotFoundError("Shot", shot_id)

    text = body.text_override or shot_found.get("voiceover_text", "")
    if not text or not text.strip():
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail="No voiceover text available for this shot (voiceover_text is empty and no text_override provided)",
        )

    # Create GenerationTask
    biz_key = f"shot:{shot_id}"
    gen_task = GenerationTask(
        tenant_id=1,
        project_id=project_id,
        task_type="voiceover_generate",
        biz_key=biz_key,
        model_provider="qwen",
        model_name="qwen3-tts",
        input_ref={
            "shot_id": shot_id,
            "text": text,
            "voice": body.voice_name,
            "speed": body.speed,
        },
        status="processing",
    )
    db.add(gen_task)
    await db.flush()
    await db.refresh(gen_task)

    await _update_shot_status(project_id, shot_id, "audio_generating")

    try:
        gateway = QwenTTSGateway()
        audio_bytes = await gateway.synthesize(
            text=text,
            voice=body.voice_name,
            speed=body.speed,
        )

        filename = f"voiceover_{uuid.uuid4().hex[:8]}.mp3"
        object_key = build_object_key(project_id, shot_id, "voiceover", filename)
        upload_bytes(object_key, audio_bytes, content_type="audio/mpeg")

        asset = AssetFile(
            tenant_id=1,
            project_id=project_id,
            asset_type="audio",
            usage_type="tts",
            mime_type="audio/mpeg",
            file_name=filename,
            object_key=object_key,
            file_size=len(audio_bytes),
            status="active",
        )
        db.add(asset)
        await db.flush()
        await db.refresh(asset)

        gen_task.status = "completed"
        gen_task.output_ref = {"asset_id": asset.id}
        await db.flush()
        await db.refresh(gen_task)

        await _update_shot_status(project_id, shot_id, "ready")

    except Exception as e:
        logger.error("TTS synthesis failed for shot %s: %s", shot_id, e)
        gen_task.status = "failed"
        gen_task.error_message = str(e)
        await db.flush()
        await db.refresh(gen_task)

        await _update_shot_status(project_id, shot_id, "failed")

    return ApiResponse(data=GenerationTaskOut.model_validate(gen_task))


@router.get(
    "/projects/{project_id}/audio/voiceovers",
    response_model=ApiResponse[PagedData[AssetOut]],
)
async def list_voiceovers(
    project_id: int,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PagedData[AssetOut]]:
    """List all voiceover (TTS) assets for a project."""
    # Count total
    count_stmt = (
        select(sa_func.count())
        .select_from(AssetFile)
        .where(
            AssetFile.project_id == project_id,
            AssetFile.asset_type == "audio",
            AssetFile.usage_type == "tts",
            AssetFile.status == "active",
        )
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    # Fetch page
    stmt = (
        select(AssetFile)
        .where(
            AssetFile.project_id == project_id,
            AssetFile.asset_type == "audio",
            AssetFile.usage_type == "tts",
            AssetFile.status == "active",
        )
        .order_by(AssetFile.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    assets = list(result.scalars().all())

    items: list[AssetOut] = []
    for asset in assets:
        try:
            url = get_presigned_url(asset.object_key)
        except Exception:
            url = None
        out = AssetOut.model_validate(asset)
        out.presigned_url = url
        items.append(out)

    return ApiResponse(
        data=PagedData(items=items, total=total, page=page, page_size=page_size)
    )
