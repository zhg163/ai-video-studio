"""Timeline endpoints — assemble, list, get, update, confirm, clip operations.

Timeline is the final assembly object for producing a finished video.
It is stored in MongoDB as a TimelineDocument with tracks, clips, subtitles,
and transitions. Auto-assembly reads from a confirmed storyboard and creates
a video track from the shots' selected assets.

Endpoints:
  POST   /assemble                       — Auto-assemble from storyboard
  GET    /                               — List timeline versions
  GET    /{version_id}                   — Get timeline detail
  PUT    /{version_id}                   — Update timeline (manual edits)
  POST   /{version_id}/confirm           — Confirm a timeline version
  POST   /{version_id}/clips/reorder     — Reorder clips within a track
  POST   /{version_id}/clips/replace     — Replace a clip's asset
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
from services.api_service.app.schemas.api_schemas import (
    AssembleTimelineRequest,
    ClipReorderRequest,
    ClipReplaceRequest,
    TimelineOut,
    TimelineUpdate,
)

router = APIRouter(prefix="/projects/{project_id}/timelines", tags=["timelines"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _doc_to_timeline_out(doc: dict) -> TimelineOut:
    """Convert a MongoDB timeline document to TimelineOut schema."""
    doc["id"] = str(doc.pop("_id"))
    doc.setdefault("created_at", datetime.now(timezone.utc))
    doc.setdefault("tracks", [])
    doc.setdefault("subtitle_segments", [])
    doc.setdefault("transitions", [])
    doc.setdefault("duration_ms", 0)
    return TimelineOut.model_validate(doc)


def _compute_duration_ms(tracks: list[dict]) -> int:
    """Compute the total timeline duration from all tracks' clips."""
    max_end = 0
    for track in tracks:
        for clip in track.get("clips", []):
            end = clip.get("end_ms", 0)
            if end > max_end:
                max_end = end
    return max_end


# ---------------------------------------------------------------------------
# Assemble
# ---------------------------------------------------------------------------


@router.post("/assemble", response_model=ApiResponse[TimelineOut])
async def assemble_timeline(
    project_id: int,
    body: AssembleTimelineRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TimelineOut]:
    """Auto-assemble a timeline from a storyboard.

    Reads all shots from the storyboard, creates a video track with clips
    ordered by scene/shot order. Each clip's duration matches the shot's
    duration_sec. Optionally attaches voiceover and BGM tracks.

    Transitions are inserted between consecutive video clips if
    default_transition is not 'cut' and transition_duration_ms > 0.
    """
    from packages.domain.models import Project

    # Verify project exists
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project", project_id)

    # Fetch storyboard from MongoDB
    mongo_db = get_mongo_db()
    sb_coll = mongo_db[Collections.STORYBOARD]

    try:
        sb_oid = ObjectId(body.storyboard_version_id)
    except Exception:
        raise NotFoundError("Storyboard", body.storyboard_version_id)

    sb_doc = await sb_coll.find_one({"_id": sb_oid, "project_id": project_id})
    if sb_doc is None:
        raise NotFoundError("Storyboard", body.storyboard_version_id)

    # Build video track from shots
    video_clips: list[dict] = []
    subtitle_segments: list[dict] = []
    current_ms = 0

    for scene in sb_doc.get("scenes", []):
        for shot in scene.get("shots", []):
            shot_id = shot.get("shot_id", f"shot_{uuid.uuid4().hex[:8]}")
            duration_ms = int(shot.get("duration_sec", 4.0) * 1000)

            # Pick the first selected asset, or None
            selected_ids = shot.get("selected_asset_ids", [])
            asset_id = selected_ids[0] if selected_ids else None

            clip_id = f"clip_{uuid.uuid4().hex[:8]}"
            video_clips.append({
                "clip_id": clip_id,
                "source_shot_id": shot_id,
                "source_asset_id": asset_id,
                "start_ms": current_ms,
                "end_ms": current_ms + duration_ms,
                "offset_ms": 0,
                "volume": None,
                "speed": 1.0,
            })

            # Auto-generate subtitle segment from voiceover_text
            voiceover_text = shot.get("voiceover_text", "")
            if voiceover_text:
                subtitle_segments.append({
                    "id": f"sub_{uuid.uuid4().hex[:8]}",
                    "start_ms": current_ms,
                    "end_ms": current_ms + duration_ms,
                    "text": voiceover_text,
                })

            current_ms += duration_ms

    # Build tracks
    tracks: list[dict] = []

    # Video track
    tracks.append({
        "track_id": "video_main",
        "track_type": "video",
        "clips": video_clips,
    })

    # Voiceover track (if asset provided)
    if body.voiceover_asset_id is not None:
        tracks.append({
            "track_id": "voiceover_main",
            "track_type": "voiceover",
            "clips": [{
                "clip_id": f"clip_{uuid.uuid4().hex[:8]}",
                "source_shot_id": "",
                "source_asset_id": body.voiceover_asset_id,
                "start_ms": 0,
                "end_ms": current_ms,
                "offset_ms": 0,
                "volume": 1.0,
                "speed": 1.0,
            }],
        })

    # BGM track (if asset provided)
    if body.bgm_asset_id is not None:
        tracks.append({
            "track_id": "bgm_main",
            "track_type": "bgm",
            "clips": [{
                "clip_id": f"clip_{uuid.uuid4().hex[:8]}",
                "source_shot_id": "",
                "source_asset_id": body.bgm_asset_id,
                "start_ms": 0,
                "end_ms": current_ms,
                "offset_ms": 0,
                "volume": 0.3,  # Default BGM lower than voiceover
                "speed": 1.0,
            }],
        })

    # Build transitions between consecutive video clips
    transitions: list[dict] = []
    if (
        body.default_transition != "cut"
        and body.transition_duration_ms > 0
        and len(video_clips) > 1
    ):
        for i in range(len(video_clips) - 1):
            transitions.append({
                "id": f"tr_{uuid.uuid4().hex[:8]}",
                "from_clip_id": video_clips[i]["clip_id"],
                "to_clip_id": video_clips[i + 1]["clip_id"],
                "type": body.default_transition,
                "duration_ms": body.transition_duration_ms,
            })

    # Determine version number
    tl_coll = mongo_db[Collections.TIMELINE]
    existing_count = await tl_coll.count_documents({"project_id": project_id})
    version_no = existing_count + 1

    duration_ms = _compute_duration_ms(tracks)

    # Store in MongoDB
    doc = {
        "project_id": project_id,
        "version_no": version_no,
        "storyboard_version_id": body.storyboard_version_id,
        "tracks": tracks,
        "subtitle_segments": subtitle_segments,
        "transitions": transitions,
        "duration_ms": duration_ms,
        "created_at": datetime.now(timezone.utc),
    }
    insert_result = await tl_coll.insert_one(doc)
    doc["_id"] = insert_result.inserted_id

    return ApiResponse(data=_doc_to_timeline_out(doc))


# ---------------------------------------------------------------------------
# List / Get
# ---------------------------------------------------------------------------


@router.get("", response_model=ApiResponse[PagedData[TimelineOut]])
async def list_timelines(
    project_id: int,
    page: int = 1,
    page_size: int = 20,
) -> ApiResponse[PagedData[TimelineOut]]:
    """List all timeline versions for a project."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.TIMELINE]

    query = {"project_id": project_id}
    total = await coll.count_documents(query)
    cursor = (
        coll.find(query)
        .sort("version_no", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    docs = await cursor.to_list(length=page_size)

    items = [_doc_to_timeline_out(doc) for doc in docs]
    return ApiResponse(
        data=PagedData(items=items, total=total, page=page, page_size=page_size)
    )


@router.get("/{version_id}", response_model=ApiResponse[TimelineOut])
async def get_timeline(
    project_id: int, version_id: str
) -> ApiResponse[TimelineOut]:
    """Get a specific timeline version."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.TIMELINE]

    try:
        oid = ObjectId(version_id)
    except Exception:
        raise NotFoundError("Timeline", version_id)

    doc = await coll.find_one({"_id": oid, "project_id": project_id})
    if doc is None:
        raise NotFoundError("Timeline", version_id)

    return ApiResponse(data=_doc_to_timeline_out(doc))


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


@router.put("/{version_id}", response_model=ApiResponse[TimelineOut])
async def update_timeline(
    project_id: int,
    version_id: str,
    body: TimelineUpdate,
) -> ApiResponse[TimelineOut]:
    """Update a timeline's tracks, subtitles, or transitions."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.TIMELINE]

    try:
        oid = ObjectId(version_id)
    except Exception:
        raise NotFoundError("Timeline", version_id)

    update_data = body.model_dump(exclude_unset=True)

    if not update_data:
        doc = await coll.find_one({"_id": oid, "project_id": project_id})
        if doc is None:
            raise NotFoundError("Timeline", version_id)
        return ApiResponse(data=_doc_to_timeline_out(doc))

    # Recompute duration if tracks changed
    if "tracks" in update_data:
        update_data["duration_ms"] = _compute_duration_ms(update_data["tracks"])

    result = await coll.find_one_and_update(
        {"_id": oid, "project_id": project_id},
        {"$set": update_data},
        return_document=True,
    )
    if result is None:
        raise NotFoundError("Timeline", version_id)

    return ApiResponse(data=_doc_to_timeline_out(result))


# ---------------------------------------------------------------------------
# Confirm
# ---------------------------------------------------------------------------


@router.post("/{version_id}/confirm", response_model=ApiResponse[TimelineOut])
async def confirm_timeline(
    project_id: int,
    version_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TimelineOut]:
    """Confirm a timeline version, updating the project's current_timeline_version_id.

    Also creates a ProjectVersion record and transitions the project status.
    """
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.TIMELINE]

    try:
        oid = ObjectId(version_id)
    except Exception:
        raise NotFoundError("Timeline", version_id)

    doc = await coll.find_one({"_id": oid, "project_id": project_id})
    if doc is None:
        raise NotFoundError("Timeline", version_id)

    from packages.domain.models import Project, ProjectVersion

    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project", project_id)

    pv = ProjectVersion(
        project_id=project_id,
        version_type="timeline",
        version_no=doc["version_no"],
        source_id=version_id,
        created_by=1,
    )
    db.add(pv)
    await db.flush()
    await db.refresh(pv)

    project.current_timeline_version_id = pv.id
    if project.status in (
        "draft", "brief_confirmed", "script_confirmed", "storyboard_confirmed",
    ):
        project.status = "timeline_confirmed"
    await db.flush()

    return ApiResponse(data=_doc_to_timeline_out(doc))


# ---------------------------------------------------------------------------
# Clip operations
# ---------------------------------------------------------------------------


@router.post(
    "/{version_id}/clips/reorder",
    response_model=ApiResponse[TimelineOut],
)
async def reorder_clips(
    project_id: int,
    version_id: str,
    body: ClipReorderRequest,
) -> ApiResponse[TimelineOut]:
    """Reorder clips within a specific track.

    Recalculates start_ms/end_ms based on the new order while preserving
    each clip's original duration.
    """
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.TIMELINE]

    try:
        oid = ObjectId(version_id)
    except Exception:
        raise NotFoundError("Timeline", version_id)

    doc = await coll.find_one({"_id": oid, "project_id": project_id})
    if doc is None:
        raise NotFoundError("Timeline", version_id)

    # Find the target track
    target_track = None
    for track in doc.get("tracks", []):
        if track["track_id"] == body.track_id:
            target_track = track
            break

    if target_track is None:
        raise NotFoundError("Track", body.track_id)

    # Build a map of clip_id -> clip
    clip_map = {c["clip_id"]: c for c in target_track["clips"]}

    # Validate all clip IDs exist
    for cid in body.clip_ids:
        if cid not in clip_map:
            raise NotFoundError("Clip", cid)

    # Reorder: recalculate start_ms/end_ms in new order
    reordered: list[dict] = []
    current_ms = 0
    for cid in body.clip_ids:
        clip = clip_map[cid]
        duration = clip["end_ms"] - clip["start_ms"]
        clip["start_ms"] = current_ms
        clip["end_ms"] = current_ms + duration
        reordered.append(clip)
        current_ms += duration

    # Include any clips not in the reorder list (append at end)
    for cid, clip in clip_map.items():
        if cid not in body.clip_ids:
            duration = clip["end_ms"] - clip["start_ms"]
            clip["start_ms"] = current_ms
            clip["end_ms"] = current_ms + duration
            reordered.append(clip)
            current_ms += duration

    target_track["clips"] = reordered

    # Recompute total duration
    duration_ms = _compute_duration_ms(doc["tracks"])

    result = await coll.find_one_and_update(
        {"_id": oid},
        {"$set": {"tracks": doc["tracks"], "duration_ms": duration_ms}},
        return_document=True,
    )

    return ApiResponse(data=_doc_to_timeline_out(result))


@router.post(
    "/{version_id}/clips/replace",
    response_model=ApiResponse[TimelineOut],
)
async def replace_clip_asset(
    project_id: int,
    version_id: str,
    body: ClipReplaceRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TimelineOut]:
    """Replace the underlying asset of a clip.

    Validates the new asset exists and belongs to the project,
    then updates the clip's source_asset_id.
    """
    from packages.domain.models import AssetFile

    # Verify new asset exists
    stmt = select(AssetFile).where(
        AssetFile.id == body.new_asset_id,
        AssetFile.project_id == project_id,
    )
    result = await db.execute(stmt)
    asset = result.scalar_one_or_none()
    if asset is None:
        raise NotFoundError("AssetFile", body.new_asset_id)

    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.TIMELINE]

    try:
        oid = ObjectId(version_id)
    except Exception:
        raise NotFoundError("Timeline", version_id)

    doc = await coll.find_one({"_id": oid, "project_id": project_id})
    if doc is None:
        raise NotFoundError("Timeline", version_id)

    # Find and update the clip
    found = False
    for track in doc.get("tracks", []):
        if track["track_id"] == body.track_id:
            for clip in track.get("clips", []):
                if clip["clip_id"] == body.clip_id:
                    clip["source_asset_id"] = body.new_asset_id
                    # Update duration if the new asset has duration info
                    if asset.duration_ms:
                        duration = clip["end_ms"] - clip["start_ms"]
                        clip["end_ms"] = clip["start_ms"] + asset.duration_ms
                    found = True
                    break
            break

    if not found:
        raise NotFoundError("Clip", body.clip_id)

    duration_ms = _compute_duration_ms(doc["tracks"])

    result = await coll.find_one_and_update(
        {"_id": oid},
        {"$set": {"tracks": doc["tracks"], "duration_ms": duration_ms}},
        return_document=True,
    )

    return ApiResponse(data=_doc_to_timeline_out(result))
