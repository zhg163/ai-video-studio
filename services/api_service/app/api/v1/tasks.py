"""Task query endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from packages.common.response import ApiResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}")
async def get_task(task_id: str) -> ApiResponse:
    return ApiResponse(data=None)


@router.post("/{task_id}/retry")
async def retry_task(task_id: str) -> ApiResponse:
    return ApiResponse(data=None)


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str) -> ApiResponse:
    return ApiResponse(data=None)
