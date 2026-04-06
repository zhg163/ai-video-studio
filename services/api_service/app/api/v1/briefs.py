"""Brief endpoints - generate, list, detail, update, confirm."""

from __future__ import annotations

from fastapi import APIRouter

from packages.common.response import ApiResponse, TaskAccepted

router = APIRouter(prefix="/projects/{project_id}/briefs", tags=["briefs"])


@router.post("/generate", response_model=ApiResponse[TaskAccepted])
async def generate_brief(project_id: int) -> ApiResponse[TaskAccepted]:
    # TODO: dispatch to agent-workflow-service
    return ApiResponse(
        message="accepted",
        data=TaskAccepted(task_id="task_placeholder", status="queued"),
    )


@router.get("")
async def list_briefs(project_id: int) -> ApiResponse:
    # TODO: query MongoDB for brief versions
    return ApiResponse(data=[])


@router.get("/{version_id}")
async def get_brief(project_id: int, version_id: str) -> ApiResponse:
    # TODO: query MongoDB
    return ApiResponse(data=None)


@router.put("/{version_id}")
async def update_brief(project_id: int, version_id: str) -> ApiResponse:
    # TODO: update brief in MongoDB
    return ApiResponse(data=None)


@router.post("/{version_id}/confirm")
async def confirm_brief(project_id: int, version_id: str) -> ApiResponse:
    # TODO: confirm brief, update project status
    return ApiResponse(data=None)
