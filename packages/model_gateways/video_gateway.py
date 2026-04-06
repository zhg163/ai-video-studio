"""Video Generation Gateway."""

from __future__ import annotations

from abc import ABC, abstractmethod


class VideoGateway(ABC):
    """Abstract interface for video generation."""

    @abstractmethod
    async def generate(self, prompt: str, image_url: str | None = None, **kwargs) -> str:
        """Generate a video. Returns a task ID or URL."""
        ...


class KlingVideoGateway(VideoGateway):
    """Kling 3.0 implementation (placeholder)."""

    async def generate(self, prompt: str, image_url: str | None = None, **kwargs) -> str:
        raise NotImplementedError("Kling Video integration not yet implemented")
