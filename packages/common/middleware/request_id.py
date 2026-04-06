"""Request ID middleware for tracing.

Uses pure ASGI middleware (not BaseHTTPMiddleware) to avoid spawning
a separate task for the inner app, which breaks asyncpg's single-task
connection constraint.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

import structlog
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

logger = structlog.get_logger()


class RequestIdMiddleware:
    """Inject a unique request_id into each request and catch unhandled exceptions.

    Implemented as a pure ASGI middleware to avoid the task-spawning behavior
    of Starlette's BaseHTTPMiddleware, which causes issues with asyncpg.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Extract or generate request ID
        request = Request(scope)
        rid = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:12]}")
        request_id_ctx.set(rid)
        scope.setdefault("state", {})
        scope["state"]["request_id"] = rid

        # Track if we already started sending a response
        response_started = False

        async def send_with_request_id(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
                # Add X-Request-ID header
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", rid.encode()))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception as exc:
            if response_started:
                # Can't send error response after headers already sent
                raise
            logger.exception("unhandled_error", request_id=rid, error=str(exc))
            error_response = JSONResponse(
                status_code=500,
                content={
                    "code": 500,
                    "message": "Internal Server Error",
                    "data": None,
                    "request_id": rid,
                },
            )
            await error_response(scope, receive, send)
