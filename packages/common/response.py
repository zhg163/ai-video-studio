"""Unified API response model."""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response envelope."""

    code: int = 0
    message: str = "ok"
    data: T | None = None
    request_id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:12]}")


class PagedData(BaseModel, Generic[T]):
    """Paged data wrapper."""

    items: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20


class TaskAccepted(BaseModel):
    """Response for async task acceptance."""

    task_id: str
    status: str = "queued"
