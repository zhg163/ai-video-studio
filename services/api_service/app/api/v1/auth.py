"""Auth stub endpoints (MVP)."""

from __future__ import annotations

from fastapi import APIRouter

from packages.common.response import ApiResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login() -> ApiResponse:
    # TODO: implement real auth
    return ApiResponse(data={"token": "dev-token-placeholder"})


@router.post("/logout")
async def logout() -> ApiResponse:
    return ApiResponse(message="logged out")


@router.get("/me")
async def me() -> ApiResponse:
    # TODO: get from JWT
    return ApiResponse(data={"id": 1, "display_name": "Dev User", "role": "owner"})
