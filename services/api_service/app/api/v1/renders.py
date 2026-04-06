"""Render/Export endpoints.

Endpoints:
  - POST /projects/{project_id}/renders       — Create a render task (sync MVP)
  - GET  /projects/{project_id}/renders        — List render tasks for a project
  - GET  /projects/{project_id}/renders/{id}   — Get render task detail
  - GET  /projects/{project_id}/renders/{id}/download — Redirect to download URL

The render flow (MVP, synchronous):
  1. Read the Timeline from MongoDB
  2. Resolve each clip's source_asset_id to an AssetFile (get MinIO object_key)
  3. Download all assets from MinIO to a temp work directory
  4. Build a RenderPlan and call FFmpegRenderer
  5. Upload the final MP4 + cover image to MinIO
  6. Create AssetFile records and update RenderTask
"""

from __future__ import annotations

import logging
import os
import tempfile
import uuid

from bson import ObjectId
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from packages.common.database import get_db
from packages.common.exceptions import NotFoundError
from packages.common.mongo import Collections, get_mongo_db
from packages.common.response import ApiResponse, PagedData
from packages.common.storage import get_presigned_url, upload_bytes
from packages.domain.models import AssetFile, Project, RenderTask
from services.api_service.app.schemas.api_schemas import (
    CreateRenderRequest,
    RenderTaskOut,
)
from services.media_render_service.app.ffmpeg.renderer import (
    FFmpegRenderer,
    RenderAudioTrack,
    RenderClip,
    RenderPlan,
    RenderSubtitle,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/renders", tags=["renders"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _task_to_out(
    task: RenderTask,
    output_url: str | None = None,
    cover_url: str | None = None,
) -> RenderTaskOut:
    """Convert a RenderTask ORM object to RenderTaskOut."""
    out = RenderTaskOut.model_validate(task)
    out.output_url = output_url
    out.cover_url = cover_url
    return out


async def _download_asset_to_dir(
    asset: AssetFile, work_dir: str
) -> str:
    """Download an asset from MinIO to the work directory.

    Returns the local file path.
    """
    from minio import Minio
    from packages.common.storage import get_minio
    from packages.common.config import settings

    client = get_minio()
    ext = os.path.splitext(asset.file_name)[1] or ".bin"
    local_name = f"asset_{asset.id}{ext}"
    local_path = os.path.join(work_dir, local_name)

    client.fget_object(
        settings.minio_bucket,
        asset.object_key,
        local_path,
    )
    return local_path


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=ApiResponse[RenderTaskOut])
async def create_render(
    project_id: int,
    body: CreateRenderRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[RenderTaskOut]:
    """Create and execute a render/export task.

    MVP: synchronous execution. The response includes the completed (or failed)
    RenderTask with output_url if successful.
    """
    # 1. Verify project exists
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project", project_id)

    # 2. Read timeline from MongoDB
    mongo_db = get_mongo_db()
    tl_coll = mongo_db[Collections.TIMELINE]

    try:
        tl_oid = ObjectId(body.timeline_version_id)
    except Exception:
        raise NotFoundError("Timeline", body.timeline_version_id)

    tl_doc = await tl_coll.find_one({"_id": tl_oid, "project_id": project_id})
    if tl_doc is None:
        raise NotFoundError("Timeline", body.timeline_version_id)

    # 3. Create RenderTask record (status=running)
    render_profile = f"{body.resolution.value}_{body.format.value}"
    render_task = RenderTask(
        project_id=project_id,
        timeline_version_id=None,  # Will be populated if we have PG version ID
        render_profile=render_profile,
        status="running",
        progress=0,
        created_by=1,
    )
    db.add(render_task)
    await db.flush()
    await db.refresh(render_task)

    work_dir = tempfile.mkdtemp(prefix=f"render_{render_task.id}_")

    try:
        # 4. Build render plan from timeline
        plan = await _build_render_plan(
            tl_doc=tl_doc,
            project_id=project_id,
            work_dir=work_dir,
            resolution=body.resolution.value,
            fmt=body.format.value,
            burn_subtitle=body.burn_subtitle,
            db=db,
        )

        # Update progress
        render_task.progress = 30
        await db.flush()

        # 5. Execute FFmpeg render
        renderer = FFmpegRenderer(work_dir=work_dir)
        output_path = await renderer.render(plan)

        render_task.progress = 80
        await db.flush()

        # 6. Extract cover frame
        cover_path = await renderer.extract_cover(output_path, timestamp_ms=1000)

        # 7. Upload output to MinIO
        output_filename = f"export_{uuid.uuid4().hex[:8]}.{body.format.value}"
        output_object_key = f"projects/{project_id}/exports/{output_filename}"

        with open(output_path, "rb") as f:
            output_bytes = f.read()

        mime_type = "video/mp4" if body.format.value == "mp4" else "video/quicktime"
        upload_bytes(output_object_key, output_bytes, content_type=mime_type)

        # Create output AssetFile
        output_asset = AssetFile(
            tenant_id=1,
            project_id=project_id,
            asset_type="video",
            usage_type="export",
            mime_type=mime_type,
            file_name=output_filename,
            object_key=output_object_key,
            file_size=len(output_bytes),
            duration_ms=tl_doc.get("duration_ms", 0),
            status="active",
        )
        db.add(output_asset)
        await db.flush()
        await db.refresh(output_asset)

        # 8. Upload cover image
        cover_object_key = f"projects/{project_id}/exports/cover_{uuid.uuid4().hex[:8]}.png"
        with open(cover_path, "rb") as f:
            cover_bytes = f.read()
        upload_bytes(cover_object_key, cover_bytes, content_type="image/png")

        cover_asset = AssetFile(
            tenant_id=1,
            project_id=project_id,
            asset_type="image",
            usage_type="cover",
            mime_type="image/png",
            file_name=os.path.basename(cover_object_key),
            object_key=cover_object_key,
            file_size=len(cover_bytes),
            status="active",
        )
        db.add(cover_asset)
        await db.flush()
        await db.refresh(cover_asset)

        # 9. Update RenderTask to success
        render_task.status = "success"
        render_task.progress = 100
        render_task.output_asset_id = output_asset.id
        await db.flush()
        await db.refresh(render_task)

        # Get presigned URLs for the response
        try:
            output_url = get_presigned_url(output_object_key)
        except Exception:
            output_url = None
        try:
            cover_url = get_presigned_url(cover_object_key)
        except Exception:
            cover_url = None

        # Cleanup
        renderer.cleanup()

        return ApiResponse(data=_task_to_out(render_task, output_url, cover_url))

    except Exception as e:
        logger.error("Render failed for project %d: %s", project_id, e)
        render_task.status = "failed"
        render_task.error_message = str(e)
        render_task.progress = 0
        await db.flush()
        await db.refresh(render_task)

        return ApiResponse(data=_task_to_out(render_task))


@router.get("", response_model=ApiResponse[PagedData[RenderTaskOut]])
async def list_renders(
    project_id: int,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PagedData[RenderTaskOut]]:
    """List all render tasks for a project."""
    # Count total
    count_stmt = (
        select(sa_func.count())
        .select_from(RenderTask)
        .where(RenderTask.project_id == project_id)
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    # Fetch page
    stmt = (
        select(RenderTask)
        .where(RenderTask.project_id == project_id)
        .order_by(RenderTask.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    tasks = list(result.scalars().all())

    items: list[RenderTaskOut] = []
    for task in tasks:
        output_url = None
        if task.output_asset_id:
            try:
                asset_stmt = select(AssetFile).where(AssetFile.id == task.output_asset_id)
                asset_result = await db.execute(asset_stmt)
                asset = asset_result.scalar_one_or_none()
                if asset:
                    output_url = get_presigned_url(asset.object_key)
            except Exception:
                pass
        items.append(_task_to_out(task, output_url))

    return ApiResponse(
        data=PagedData(items=items, total=total, page=page, page_size=page_size)
    )


@router.get("/{render_id}", response_model=ApiResponse[RenderTaskOut])
async def get_render(
    project_id: int,
    render_id: int,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[RenderTaskOut]:
    """Get a specific render task."""
    stmt = select(RenderTask).where(
        RenderTask.id == render_id,
        RenderTask.project_id == project_id,
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if task is None:
        raise NotFoundError("RenderTask", render_id)

    output_url = None
    if task.output_asset_id:
        try:
            asset_stmt = select(AssetFile).where(AssetFile.id == task.output_asset_id)
            asset_result = await db.execute(asset_stmt)
            asset = asset_result.scalar_one_or_none()
            if asset:
                output_url = get_presigned_url(asset.object_key)
        except Exception:
            pass

    return ApiResponse(data=_task_to_out(task, output_url))


@router.get("/{render_id}/download")
async def download_render(
    project_id: int,
    render_id: int,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Redirect to the presigned download URL for the rendered video."""
    stmt = select(RenderTask).where(
        RenderTask.id == render_id,
        RenderTask.project_id == project_id,
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if task is None:
        raise NotFoundError("RenderTask", render_id)

    if task.status != "success" or task.output_asset_id is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail="Render task has not completed successfully",
        )

    asset_stmt = select(AssetFile).where(AssetFile.id == task.output_asset_id)
    asset_result = await db.execute(asset_stmt)
    asset = asset_result.scalar_one_or_none()
    if asset is None:
        raise NotFoundError("Output AssetFile", task.output_asset_id)

    url = get_presigned_url(asset.object_key)
    return RedirectResponse(url=url)


# ---------------------------------------------------------------------------
# Render plan builder
# ---------------------------------------------------------------------------


async def _build_render_plan(
    tl_doc: dict,
    project_id: int,
    work_dir: str,
    resolution: str,
    fmt: str,
    burn_subtitle: bool,
    db: AsyncSession,
) -> RenderPlan:
    """Build a RenderPlan from a timeline document.

    Downloads all referenced assets from MinIO to the work directory.
    """
    plan = RenderPlan(
        resolution=resolution,
        format=fmt,
        burn_subtitle=burn_subtitle,
        duration_ms=tl_doc.get("duration_ms", 0),
    )

    # Collect all asset IDs we need to download
    asset_id_set: set[int] = set()
    for track in tl_doc.get("tracks", []):
        for clip in track.get("clips", []):
            aid = clip.get("source_asset_id")
            if aid is not None:
                asset_id_set.add(aid)

    # Batch-load all assets from PostgreSQL
    asset_map: dict[int, AssetFile] = {}
    if asset_id_set:
        stmt = select(AssetFile).where(AssetFile.id.in_(asset_id_set))
        result = await db.execute(stmt)
        for asset in result.scalars().all():
            asset_map[asset.id] = asset

    # Download assets to work_dir and build local path map
    local_paths: dict[int, str] = {}
    for aid, asset in asset_map.items():
        try:
            local_path = await _download_asset_to_dir(asset, work_dir)
            local_paths[aid] = local_path
        except Exception as e:
            logger.warning("Failed to download asset %d: %s", aid, e)

    # Build video clips
    for track in tl_doc.get("tracks", []):
        track_type = track.get("track_type", "video")

        if track_type == "video":
            for clip in track.get("clips", []):
                aid = clip.get("source_asset_id")
                if aid and aid in local_paths:
                    plan.video_clips.append(RenderClip(
                        clip_id=clip.get("clip_id", ""),
                        file_path=local_paths[aid],
                        start_ms=clip.get("start_ms", 0),
                        end_ms=clip.get("end_ms", 0),
                        speed=clip.get("speed", 1.0),
                    ))

        elif track_type in ("voiceover", "bgm"):
            for clip in track.get("clips", []):
                aid = clip.get("source_asset_id")
                if aid and aid in local_paths:
                    plan.audio_tracks.append(RenderAudioTrack(
                        track_type=track_type,
                        file_path=local_paths[aid],
                        volume=clip.get("volume", 1.0) if clip.get("volume") is not None else (0.3 if track_type == "bgm" else 1.0),
                        start_ms=clip.get("start_ms", 0),
                        end_ms=clip.get("end_ms", 0),
                    ))

    # Build subtitles
    for seg in tl_doc.get("subtitle_segments", []):
        plan.subtitles.append(RenderSubtitle(
            start_ms=seg.get("start_ms", 0),
            end_ms=seg.get("end_ms", 0),
            text=seg.get("text", ""),
        ))

    # Build transitions
    for tr in tl_doc.get("transitions", []):
        plan.transitions.append(RenderTransition(
            from_clip_id=tr.get("from_clip_id", ""),
            to_clip_id=tr.get("to_clip_id", ""),
            type=tr.get("type", "fade"),
            duration_ms=tr.get("duration_ms", 300),
        ))

    return plan
