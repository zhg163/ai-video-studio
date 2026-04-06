"""Shot media generation endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from packages.common.response import ApiResponse, TaskAccepted

router = APIRouter(prefix="/projects/{project_id}/shots", tags=["shots"])


@router.post("/{shot_id}/images/generate")
async def generate_keyframe(project_id: int, shot_id: str) -> ApiResponse[TaskAccepted]:
    return ApiResponse(
        message="accepted",
        data=TaskAccepted(task_id="task_placeholder", status="queued"),
    )


@router.post("/{shot_id}/videos/generate")
async def generate_video(project_id: int, shot_id: str) -> ApiResponse[TaskAccepted]:
    return ApiResponse(
        message="accepted",
        data=TaskAccepted(task_id="task_placeholder", status="queued"),
    )


@router.post("/{shot_id}/audios/generate")
async def generate_audio(project_id: int, shot_id: str) -> ApiResponse[TaskAccepted]:
    return ApiResponse(
        message="accepted",
        data=TaskAccepted(task_id="task_placeholder", status="queued"),
    )


@router.put("/{shot_id}")
async def update_shot(project_id: int, shot_id: str) -> ApiResponse:
    return ApiResponse(data=None)


@router.delete("/{shot_id}")
async def delete_shot(project_id: int, shot_id: str) -> ApiResponse:
    return ApiResponse(message="deleted")


@router.get("/{shot_id}/assets")
async def get_shot_assets(project_id: int, shot_id: str) -> ApiResponse:
    return ApiResponse(data=[])
