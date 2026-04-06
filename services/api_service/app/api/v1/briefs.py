"""Brief endpoints - generate, list, detail, update, confirm.

Briefs are stored in MongoDB. Generation uses CreativeAgent + Qwen LLM.
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
from services.agent_workflow_service.app.agents.creative_agent import CreativeAgent
from services.api_service.app.schemas.api_schemas import BriefGenerateRequest, BriefOut, BriefUpdate

router = APIRouter(prefix="/projects/{project_id}/briefs", tags=["briefs"])


def _doc_to_brief_out(doc: dict) -> BriefOut:
    """Convert a MongoDB document to BriefOut schema."""
    doc["id"] = str(doc.pop("_id"))
    doc["created_at"] = doc.get("created_at", datetime.now(timezone.utc))
    return BriefOut.model_validate(doc)


@router.post("/generate", response_model=ApiResponse[BriefOut])
async def generate_brief(
    project_id: int,
    body: BriefGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[BriefOut]:
    """Generate a creative brief using AI from user input.

    This is a synchronous call (blocks until LLM responds).
    For production, this should be dispatched as an async task.
    """
    # Verify project exists
    from packages.domain.models import Project

    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project", project_id)

    # Determine version number
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.CREATIVE_BRIEF]
    existing_count = await coll.count_documents({"project_id": project_id})
    version_no = existing_count + 1

    # Run creative agent
    llm = QwenLLMGateway()
    agent = CreativeAgent(llm=llm)
    brief_data = await agent.run(
        project_id=project_id,
        user_input=body.text,
        references=body.references,
    )

    # Store in MongoDB
    doc = {
        "project_id": project_id,
        "version_no": version_no,
        "source_input": brief_data["source_input"],
        "structured_brief": brief_data["structured_brief"],
        "constraints": brief_data["constraints"],
        "created_by": 1,  # TODO: from auth context
        "created_at": datetime.now(timezone.utc),
    }
    insert_result = await coll.insert_one(doc)
    doc["_id"] = insert_result.inserted_id

    return ApiResponse(data=_doc_to_brief_out(doc))


@router.get("", response_model=ApiResponse[PagedData[BriefOut]])
async def list_briefs(
    project_id: int,
    page: int = 1,
    page_size: int = 20,
) -> ApiResponse[PagedData[BriefOut]]:
    """List all brief versions for a project."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.CREATIVE_BRIEF]

    query = {"project_id": project_id}
    total = await coll.count_documents(query)
    cursor = coll.find(query).sort("version_no", -1).skip((page - 1) * page_size).limit(page_size)
    docs = await cursor.to_list(length=page_size)

    items = [_doc_to_brief_out(doc) for doc in docs]
    return ApiResponse(data=PagedData(items=items, total=total, page=page, page_size=page_size))


@router.get("/{version_id}", response_model=ApiResponse[BriefOut])
async def get_brief(project_id: int, version_id: str) -> ApiResponse[BriefOut]:
    """Get a specific brief version."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.CREATIVE_BRIEF]

    try:
        oid = ObjectId(version_id)
    except Exception:
        raise NotFoundError("Brief", version_id)

    doc = await coll.find_one({"_id": oid, "project_id": project_id})
    if doc is None:
        raise NotFoundError("Brief", version_id)

    return ApiResponse(data=_doc_to_brief_out(doc))


@router.put("/{version_id}", response_model=ApiResponse[BriefOut])
async def update_brief(
    project_id: int,
    version_id: str,
    body: BriefUpdate,
) -> ApiResponse[BriefOut]:
    """Update a brief (structured_brief and/or constraints)."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.CREATIVE_BRIEF]

    try:
        oid = ObjectId(version_id)
    except Exception:
        raise NotFoundError("Brief", version_id)

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        # Nothing to update, just return current
        doc = await coll.find_one({"_id": oid, "project_id": project_id})
        if doc is None:
            raise NotFoundError("Brief", version_id)
        return ApiResponse(data=_doc_to_brief_out(doc))

    result = await coll.find_one_and_update(
        {"_id": oid, "project_id": project_id},
        {"$set": update_data},
        return_document=True,
    )
    if result is None:
        raise NotFoundError("Brief", version_id)

    return ApiResponse(data=_doc_to_brief_out(result))


@router.post("/{version_id}/confirm", response_model=ApiResponse[BriefOut])
async def confirm_brief(
    project_id: int,
    version_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[BriefOut]:
    """Confirm a brief version, updating the project's current_brief_version_id."""
    mongo_db = get_mongo_db()
    coll = mongo_db[Collections.CREATIVE_BRIEF]

    try:
        oid = ObjectId(version_id)
    except Exception:
        raise NotFoundError("Brief", version_id)

    doc = await coll.find_one({"_id": oid, "project_id": project_id})
    if doc is None:
        raise NotFoundError("Brief", version_id)

    # Update project status and brief version reference
    from packages.domain.models import Project, ProjectVersion

    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project", project_id)

    # Create a project version record
    pv = ProjectVersion(
        project_id=project_id,
        version_type="brief",
        version_no=doc["version_no"],
        source_id=version_id,
        created_by=1,  # TODO: from auth context
    )
    db.add(pv)
    await db.flush()
    await db.refresh(pv)

    # Update project's current brief version
    project.current_brief_version_id = pv.id
    if project.status == "draft":
        project.status = "brief_confirmed"
    await db.flush()

    return ApiResponse(data=_doc_to_brief_out(doc))
