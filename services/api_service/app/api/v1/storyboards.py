"""Storyboard & Shot endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from packages.common.response import ApiResponse, TaskAccepted

router = APIRouter(prefix="/projects/{project_id}/storyboards", tags=["storyboards"])


@router.post("/generate", response_model=ApiResponse[TaskAccepted])
async def generate_storyboard(project_id: int) -> ApiResponse[TaskAccepted]:
    return ApiResponse(
        message="accepted",
        data=TaskAccepted(task_id="task_placeholder", status="queued"),
    )


@router.get("")
async def list_storyboards(project_id: int) -> ApiResponse:
    return ApiResponse(data=[])


@router.get("/{version_id}")
async def get_storyboard(project_id: int, version_id: str) -> ApiResponse:
    return ApiResponse(data=None)
