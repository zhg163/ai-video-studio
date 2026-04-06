"""Timeline endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from packages.common.response import ApiResponse, TaskAccepted

router = APIRouter(prefix="/projects/{project_id}/timelines", tags=["timelines"])


@router.post("/assemble")
async def assemble_timeline(project_id: int) -> ApiResponse[TaskAccepted]:
    return ApiResponse(
        message="accepted",
        data=TaskAccepted(task_id="task_placeholder", status="queued"),
    )


@router.get("")
async def list_timelines(project_id: int) -> ApiResponse:
    return ApiResponse(data=[])


@router.get("/{version_id}")
async def get_timeline(project_id: int, version_id: str) -> ApiResponse:
    return ApiResponse(data=None)


@router.put("/{version_id}")
async def update_timeline(project_id: int, version_id: str) -> ApiResponse:
    return ApiResponse(data=None)
