"""Script endpoints - generate, list, detail, edit, regenerate."""

from __future__ import annotations

from fastapi import APIRouter

from packages.common.response import ApiResponse, TaskAccepted

router = APIRouter(prefix="/projects/{project_id}/scripts", tags=["scripts"])


@router.post("/generate", response_model=ApiResponse[TaskAccepted])
async def generate_script(project_id: int) -> ApiResponse[TaskAccepted]:
    # TODO: dispatch to agent-workflow-service
    return ApiResponse(
        message="accepted",
        data=TaskAccepted(task_id="task_placeholder", status="queued"),
    )


@router.get("")
async def list_scripts(project_id: int) -> ApiResponse:
    return ApiResponse(data=[])


@router.get("/{version_id}")
async def get_script(project_id: int, version_id: str) -> ApiResponse:
    return ApiResponse(data=None)


@router.put("/{version_id}")
async def update_script(project_id: int, version_id: str) -> ApiResponse:
    return ApiResponse(data=None)


@router.post("/{version_id}/regenerate")
async def regenerate_script(project_id: int, version_id: str) -> ApiResponse[TaskAccepted]:
    return ApiResponse(
        message="accepted",
        data=TaskAccepted(task_id="task_placeholder", status="queued"),
    )
