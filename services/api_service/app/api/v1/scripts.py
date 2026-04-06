"""Script endpoints - generate, list, detail, update, confirm.

Scripts are stored in MongoDB. Generation uses ScriptAgent + Qwen LLM.
A script requires a confirmed brief (brief_version_id).
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
from services.agent_workflow_service.app.agents.script_agent import ScriptAgent
from services.api_service.app.schemas.api_schemas import (
    ScriptGenerateRequest,
    ScriptOut,
    ScriptUpdate,
)

router = APIRouter(prefix="/projects/{project_id}/scripts", tags=["scripts"])


def _doc_to_script_out(doc: dict) -> ScriptOut:
    """Convert a MongoDB document to ScriptOut schema."""
    doc["id"] = str(doc.pop("_id"))
    doc["created_at"] = doc.get("created_at", datetime.now(timezone.utc))
    return ScriptOut.model_validate(doc)


@router.post("/generate", response_model=ApiResponse[ScriptOut])
async def generate_script(
    project_id: int,
    body: ScriptGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ScriptOut]:
    """Generate a video script from a confirmed brief.

    Requires a valid brief_version_id that exists in MongoDB.
    """
    from packages.domain.models import Project

    # Verify project exists
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project", project_id)

    # Fetch the brief from MongoDB
    mongo_db = get_mongo_db()
    brief_coll = mongo_db[Collections.CREATIVE_BRIEF]

    try:
        brief_oid = ObjectId(body.brief_version_id)
    except Exception:
        raise NotFoundError("Brief", body.brief_version_id)

    brief_doc = await brief_coll.find_one({"_id": brief_oid, "project_id": project_id})
    if brief_doc is None:
        raise NotFoundError("Brief", body.brief_version_id)

    # Determine version number
    script_coll = mongo_db[Collections.SCRIPT]
    existing_count = await script_coll.count_documents({"project_id": project_id})
    version_no = existing_count + 1

    # Run script agent
    llm = QwenLLMGateway()
    agent = ScriptAgent(llm=llm)
    brief_data = {
        "source_input": brief_doc.get("source_input", {}),
        "structured_brief": brief_doc.get("structured_brief", {}),
        "constraints": brief_doc.get("constraints", {}),
    }
    script_data = await agent.run(
        project_id=project_id,
        brief_data=brief_data,
        language=project.language,
    )

    # Store in MongoDB
    doc = {
        "project_id": project_id,
        "version_no": version_no,
        "brief_version_id": body.brief_version_id,
        "title": script_data["title"],
        "language": script_data["language"],
        "sections": script_data["sections"],
        "full_text": script_data["full_text"],
        "created_by": 1,  # TODO: from auth context
        "created_at": datetime.now(timezone.utc),
    }
    insert_result = await script_coll.insert_one(doc)
    doc["_id"] = insert_result.inserted_id

    return ApiResponse(data=_doc_to_script_out(doc))


@router.get("", response_model=ApiResponse[PagedData[ScriptOut]])
async def list_scripts(
    project_id: int,
    page: int = 1,
    page_size: int = 20,
) -> ApiResponse[PagedData[ScriptOut]]:
    """List all script versions for a project."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.SCRIPT]

    query = {"project_id": project_id}
    total = await coll.count_documents(query)
    cursor = coll.find(query).sort("version_no", -1).skip((page - 1) * page_size).limit(page_size)
    docs = await cursor.to_list(length=page_size)

    items = [_doc_to_script_out(doc) for doc in docs]
    return ApiResponse(data=PagedData(items=items, total=total, page=page, page_size=page_size))


@router.get("/{version_id}", response_model=ApiResponse[ScriptOut])
async def get_script(project_id: int, version_id: str) -> ApiResponse[ScriptOut]:
    """Get a specific script version."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.SCRIPT]

    try:
        oid = ObjectId(version_id)
    except Exception:
        raise NotFoundError("Script", version_id)

    doc = await coll.find_one({"_id": oid, "project_id": project_id})
    if doc is None:
        raise NotFoundError("Script", version_id)

    return ApiResponse(data=_doc_to_script_out(doc))


@router.put("/{version_id}", response_model=ApiResponse[ScriptOut])
async def update_script(
    project_id: int,
    version_id: str,
    body: ScriptUpdate,
) -> ApiResponse[ScriptOut]:
    """Update a script (title, sections, and/or full_text)."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.SCRIPT]

    try:
        oid = ObjectId(version_id)
    except Exception:
        raise NotFoundError("Script", version_id)

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        doc = await coll.find_one({"_id": oid, "project_id": project_id})
        if doc is None:
            raise NotFoundError("Script", version_id)
        return ApiResponse(data=_doc_to_script_out(doc))

    result = await coll.find_one_and_update(
        {"_id": oid, "project_id": project_id},
        {"$set": update_data},
        return_document=True,
    )
    if result is None:
        raise NotFoundError("Script", version_id)

    return ApiResponse(data=_doc_to_script_out(result))


@router.post("/{version_id}/confirm", response_model=ApiResponse[ScriptOut])
async def confirm_script(
    project_id: int,
    version_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ScriptOut]:
    """Confirm a script version, updating the project's current_script_version_id."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.SCRIPT]

    try:
        oid = ObjectId(version_id)
    except Exception:
        raise NotFoundError("Script", version_id)

    doc = await coll.find_one({"_id": oid, "project_id": project_id})
    if doc is None:
        raise NotFoundError("Script", version_id)

    # Update project status and script version reference
    from packages.domain.models import Project, ProjectVersion

    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project", project_id)

    # Create a project version record
    pv = ProjectVersion(
        project_id=project_id,
        version_type="script",
        version_no=doc["version_no"],
        source_id=version_id,
        created_by=1,  # TODO: from auth context
    )
    db.add(pv)
    await db.flush()
    await db.refresh(pv)

    # Update project's current script version
    project.current_script_version_id = pv.id
    if project.status in ("draft", "brief_confirmed"):
        project.status = "script_confirmed"
    await db.flush()

    return ApiResponse(data=_doc_to_script_out(doc))
