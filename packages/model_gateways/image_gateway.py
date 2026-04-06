"""Image Generation Gateway."""

from __future__ import annotations

from abc import ABC, abstractmethod


class ImageGateway(ABC):
    """Abstract interface for image generation."""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> bytes:
        """Generate an image from a prompt. Returns image bytes."""
        ...


class GPTImageGateway(ImageGateway):
    """GPT Image 1 / DALL-E implementation (placeholder)."""

    async def generate(self, prompt: str, **kwargs) -> bytes:
        raise NotImplementedError("GPT Image integration not yet implemented")


class FluxImageGateway(ImageGateway):
    """FLUX API implementation (placeholder)."""

    async def generate(self, prompt: str, **kwargs) -> bytes:
        raise NotImplementedError("FLUX Image integration not yet implemented")
