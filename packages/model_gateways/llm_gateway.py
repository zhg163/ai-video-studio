"""LLM Gateway - abstraction for text generation models."""

from __future__ import annotations

from abc import ABC, abstractmethod

from packages.common.config import settings


class LLMGateway(ABC):
    """Abstract interface for LLM text generation."""

    @abstractmethod
    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        """Generate text from a prompt."""
        ...


class QwenLLMGateway(LLMGateway):
    """Qwen API implementation (placeholder)."""

    def __init__(self) -> None:
        self.api_key = settings.qwen_api_key
        self.model = settings.qwen_model

    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        # TODO: implement actual Qwen API call via httpx
        raise NotImplementedError("Qwen LLM integration not yet implemented")
