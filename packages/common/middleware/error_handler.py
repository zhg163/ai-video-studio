"""Global exception handler middleware."""

from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse

from packages.common.exceptions import AppError
from packages.common.middleware.request_id import request_id_ctx

logger = structlog.get_logger()


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> ORJSONResponse:
        rid = request_id_ctx.get("")
        logger.warning("app_error", code=exc.code, message=exc.message, request_id=rid)
        return ORJSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
                "data": None,
                "request_id": rid,
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> ORJSONResponse:
        rid = request_id_ctx.get("")
        logger.exception("unhandled_error", request_id=rid, exc_info=exc)
        return ORJSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "Internal Server Error",
                "data": None,
                "request_id": rid,
            },
        )
