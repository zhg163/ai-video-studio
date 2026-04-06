"""Render/Export endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from packages.common.response import ApiResponse, TaskAccepted

router = APIRouter(prefix="/projects/{project_id}/renders", tags=["renders"])


@router.post("")
async def create_render(project_id: int) -> ApiResponse[TaskAccepted]:
    return ApiResponse(
        message="accepted",
        data=TaskAccepted(task_id="task_placeholder", status="queued"),
    )


@router.get("")
async def list_renders(project_id: int) -> ApiResponse:
    return ApiResponse(data=[])
