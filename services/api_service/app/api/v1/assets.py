"""Asset endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from packages.common.response import ApiResponse

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("/upload")
async def upload_asset() -> ApiResponse:
    return ApiResponse(data=None)


@router.get("/{asset_id}")
async def get_asset(asset_id: int) -> ApiResponse:
    return ApiResponse(data=None)


@router.delete("/{asset_id}")
async def delete_asset(asset_id: int) -> ApiResponse:
    return ApiResponse(message="deleted")
