"""Request ID middleware for tracing."""

from __future__ import annotations

import uuid
from contextvars import ContextVar

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

logger = structlog.get_logger()


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Inject a unique request_id into each request and catch unhandled exceptions."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        rid = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:12]}")
        request_id_ctx.set(rid)
        request.state.request_id = rid
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.exception("unhandled_error", request_id=rid, error=str(exc))
            response = JSONResponse(
                status_code=500,
                content={
                    "code": 500,
                    "message": "Internal Server Error",
                    "data": None,
                    "request_id": rid,
                },
            )
        response.headers["X-Request-ID"] = rid
        return response
