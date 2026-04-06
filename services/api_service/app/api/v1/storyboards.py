"""Storyboard & Shot endpoints - generate, list, detail, update, confirm.

Storyboards are stored in MongoDB. Generation uses StoryboardAgent + Qwen LLM.
A storyboard requires a confirmed script (script_version_id).
"""

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.common.database import get_db
from packages.common.exceptions import NotFoundError
from packages.common.mongo import Collections, get_mongo_db
from packages.common.response import ApiResponse, PagedData
from packages.model_gateways.llm_gateway import QwenLLMGateway
from services.agent_workflow_service.app.agents.storyboard_agent import StoryboardAgent
from services.api_service.app.schemas.api_schemas import (
    StoryboardGenerateRequest,
    StoryboardOut,
    StoryboardUpdate,
)

router = APIRouter(prefix="/projects/{project_id}/storyboards", tags=["storyboards"])


def _doc_to_storyboard_out(doc: dict) -> StoryboardOut:
    """Convert a MongoDB document to StoryboardOut schema."""
    doc["id"] = str(doc.pop("_id"))
    doc["created_at"] = doc.get("created_at", datetime.now(timezone.utc))
    return StoryboardOut.model_validate(doc)


@router.post("/generate", response_model=ApiResponse[StoryboardOut])
async def generate_storyboard(
    project_id: int,
    body: StoryboardGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[StoryboardOut]:
    """Generate a storyboard from a confirmed script.

    Requires a valid script_version_id that exists in MongoDB.
    """
    from packages.domain.models import Project

    # Verify project exists
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project", project_id)

    # Fetch the script from MongoDB
    mongo_db = get_mongo_db()
    script_coll = mongo_db[Collections.SCRIPT]

    try:
        script_oid = ObjectId(body.script_version_id)
    except Exception:
        raise NotFoundError("Script", body.script_version_id)

    script_doc = await script_coll.find_one({"_id": script_oid, "project_id": project_id})
    if script_doc is None:
        raise NotFoundError("Script", body.script_version_id)

    # Determine version number
    sb_coll = mongo_db[Collections.STORYBOARD]
    existing_count = await sb_coll.count_documents({"project_id": project_id})
    version_no = existing_count + 1

    # Get target duration from the brief if available
    target_duration = 30
    brief_coll = mongo_db[Collections.CREATIVE_BRIEF]
    brief_version_id = script_doc.get("brief_version_id", "")
    if brief_version_id:
        try:
            brief_doc = await brief_coll.find_one({"_id": ObjectId(brief_version_id)})
            if brief_doc:
                target_duration = brief_doc.get("structured_brief", {}).get("duration_sec", 30)
        except Exception:
            pass

    # Run storyboard agent
    llm = QwenLLMGateway()
    agent = StoryboardAgent(llm=llm)
    script_data = {
        "title": script_doc.get("title", ""),
        "sections": script_doc.get("sections", []),
        "full_text": script_doc.get("full_text", ""),
        "language": script_doc.get("language", "zh-CN"),
    }
    sb_data = await agent.run(
        project_id=project_id,
        script_data=script_data,
        target_duration_sec=target_duration,
    )

    # Store in MongoDB
    doc = {
        "project_id": project_id,
        "version_no": version_no,
        "script_version_id": body.script_version_id,
        "scenes": sb_data["scenes"],
        "created_at": datetime.now(timezone.utc),
    }
    insert_result = await sb_coll.insert_one(doc)
    doc["_id"] = insert_result.inserted_id

    return ApiResponse(data=_doc_to_storyboard_out(doc))


@router.get("", response_model=ApiResponse[PagedData[StoryboardOut]])
async def list_storyboards(
    project_id: int,
    page: int = 1,
    page_size: int = 20,
) -> ApiResponse[PagedData[StoryboardOut]]:
    """List all storyboard versions for a project."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.STORYBOARD]

    query = {"project_id": project_id}
    total = await coll.count_documents(query)
    cursor = coll.find(query).sort("version_no", -1).skip((page - 1) * page_size).limit(page_size)
    docs = await cursor.to_list(length=page_size)

    items = [_doc_to_storyboard_out(doc) for doc in docs]
    return ApiResponse(data=PagedData(items=items, total=total, page=page, page_size=page_size))


@router.get("/{version_id}", response_model=ApiResponse[StoryboardOut])
async def get_storyboard(project_id: int, version_id: str) -> ApiResponse[StoryboardOut]:
    """Get a specific storyboard version."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.STORYBOARD]

    try:
        oid = ObjectId(version_id)
    except Exception:
        raise NotFoundError("Storyboard", version_id)

    doc = await coll.find_one({"_id": oid, "project_id": project_id})
    if doc is None:
        raise NotFoundError("Storyboard", version_id)

    return ApiResponse(data=_doc_to_storyboard_out(doc))


@router.put("/{version_id}", response_model=ApiResponse[StoryboardOut])
async def update_storyboard(
    project_id: int,
    version_id: str,
    body: StoryboardUpdate,
) -> ApiResponse[StoryboardOut]:
    """Update a storyboard (scenes and their shots)."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.STORYBOARD]

    try:
        oid = ObjectId(version_id)
    except Exception:
        raise NotFoundError("Storyboard", version_id)

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        doc = await coll.find_one({"_id": oid, "project_id": project_id})
        if doc is None:
            raise NotFoundError("Storyboard", version_id)
        return ApiResponse(data=_doc_to_storyboard_out(doc))

    result = await coll.find_one_and_update(
        {"_id": oid, "project_id": project_id},
        {"$set": update_data},
        return_document=True,
    )
    if result is None:
        raise NotFoundError("Storyboard", version_id)

    return ApiResponse(data=_doc_to_storyboard_out(result))


@router.post("/{version_id}/confirm", response_model=ApiResponse[StoryboardOut])
async def confirm_storyboard(
    project_id: int,
    version_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[StoryboardOut]:
    """Confirm a storyboard version, updating the project's current_storyboard_version_id."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.STORYBOARD]

    try:
        oid = ObjectId(version_id)
    except Exception:
        raise NotFoundError("Storyboard", version_id)

    doc = await coll.find_one({"_id": oid, "project_id": project_id})
    if doc is None:
        raise NotFoundError("Storyboard", version_id)

    from packages.domain.models import Project, ProjectVersion

    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project", project_id)

    pv = ProjectVersion(
        project_id=project_id,
        version_type="storyboard",
        version_no=doc["version_no"],
        source_id=version_id,
        created_by=1,
    )
    db.add(pv)
    await db.flush()
    await db.refresh(pv)

    project.current_storyboard_version_id = pv.id
    if project.status in ("draft", "brief_confirmed", "script_confirmed"):
        project.status = "storyboard_confirmed"
    await db.flush()

    return ApiResponse(data=_doc_to_storyboard_out(doc))
