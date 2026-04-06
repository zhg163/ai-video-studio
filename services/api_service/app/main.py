"""API Service - FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from packages.common.config import settings
from packages.common.middleware import RequestIdMiddleware, register_exception_handlers, setup_logging
from packages.common.mongo import close_mongo
from packages.common.redis_client import close_redis
from services.api_service.app.api.health import router as health_router
from services.api_service.app.api.v1.assets import router as assets_router
from services.api_service.app.api.v1.auth import router as auth_router
from services.api_service.app.api.v1.briefs import router as briefs_router
from services.api_service.app.api.v1.projects import router as projects_router
from services.api_service.app.api.v1.renders import router as renders_router
from services.api_service.app.api.v1.scripts import router as scripts_router
from services.api_service.app.api.v1.shots import router as shots_router
from services.api_service.app.api.v1.storyboards import router as storyboards_router
from services.api_service.app.api.v1.tasks import router as tasks_router
from services.api_service.app.api.v1.audio import router as audio_router
from services.api_service.app.api.v1.timelines import router as timelines_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup & shutdown."""
    setup_logging("DEBUG" if settings.debug else "INFO")
    yield
    await close_mongo()
    await close_redis()


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="AI Video Studio API",
        version="0.1.0",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    register_exception_handlers(app)

    # Routers
    app.include_router(health_router)
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(briefs_router, prefix="/api/v1")
    app.include_router(scripts_router, prefix="/api/v1")
    app.include_router(storyboards_router, prefix="/api/v1")
    app.include_router(shots_router, prefix="/api/v1")
    app.include_router(assets_router, prefix="/api/v1")
    app.include_router(timelines_router, prefix="/api/v1")
    app.include_router(audio_router, prefix="/api/v1")
    app.include_router(renders_router, prefix="/api/v1")
    app.include_router(tasks_router, prefix="/api/v1")

    return app


app = create_app()
