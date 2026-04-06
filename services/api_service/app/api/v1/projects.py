"""Project CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.common.database import get_db
from packages.common.exceptions import NotFoundError
from packages.common.response import ApiResponse, PagedData
from packages.domain.models import Project
from services.api_service.app.schemas.api_schemas import ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ApiResponse[ProjectOut])
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ProjectOut]:
    # TODO: get tenant_id and owner_id from auth context
    project = Project(
        tenant_id=1,
        owner_id=1,
        name=body.name,
        description=body.description,
        aspect_ratio=body.aspect_ratio,
        language=body.language,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return ApiResponse(data=ProjectOut.model_validate(project))


@router.get("", response_model=ApiResponse[PagedData[ProjectOut]])
async def list_projects(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PagedData[ProjectOut]]:
    # TODO: filter by tenant from auth
    offset = (page - 1) * page_size
    stmt = select(Project).order_by(Project.updated_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    projects = result.scalars().all()

    count_stmt = select(Project)
    count_result = await db.execute(count_stmt)
    total = len(count_result.scalars().all())

    items = [ProjectOut.model_validate(p) for p in projects]
    return ApiResponse(data=PagedData(items=items, total=total, page=page, page_size=page_size))


@router.get("/{project_id}", response_model=ApiResponse[ProjectOut])
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ProjectOut]:
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project", project_id)
    return ApiResponse(data=ProjectOut.model_validate(project))


@router.patch("/{project_id}", response_model=ApiResponse[ProjectOut])
async def update_project(
    project_id: int,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ProjectOut]:
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project", project_id)

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    await db.flush()
    await db.refresh(project)
    return ApiResponse(data=ProjectOut.model_validate(project))


@router.post("/{project_id}/archive", response_model=ApiResponse[ProjectOut])
async def archive_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ProjectOut]:
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project", project_id)

    project.status = "archived"
    await db.flush()
    await db.refresh(project)
    return ApiResponse(data=ProjectOut.model_validate(project))
