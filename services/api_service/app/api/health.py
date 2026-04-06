"""Health check and root router."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@router.get("/")
async def root() -> dict:
    return {"service": "ai-video-studio", "version": "0.1.0"}
