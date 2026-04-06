"""LLM Gateway - abstraction for text generation models.

Qwen implementation uses DashScope compatible API (OpenAI-compatible).
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod

import httpx
import structlog

from packages.common.config import settings

logger = structlog.get_logger()


class LLMGateway(ABC):
    """Abstract interface for LLM text generation."""

    @abstractmethod
    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        """Generate text from a prompt."""
        ...

    @abstractmethod
    async def generate_json(self, prompt: str, system: str = "", **kwargs) -> dict:
        """Generate structured JSON output from a prompt."""
        ...


class QwenLLMGateway(LLMGateway):
    """Qwen API implementation via DashScope OpenAI-compatible endpoint."""

    BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.qwen_api_key
        self.model = model or settings.qwen_model
        if not self.api_key:
            raise ValueError("QWEN_API_KEY is required for QwenLLMGateway")

    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        """Generate text via Qwen chat completions API."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        logger.info(
            "llm_generate",
            model=self.model,
            prompt_len=len(prompt),
            response_len=len(content),
            usage=data.get("usage"),
        )
        return content

    async def generate_json(self, prompt: str, system: str = "", **kwargs) -> dict:
        """Generate structured JSON by instructing the model to output JSON.

        Parses the response and extracts JSON from potential markdown code blocks.
        """
        json_system = system + "\n\nYou MUST respond with valid JSON only. No markdown, no explanation."
        raw = await self.generate(prompt, system=json_system, **kwargs)

        # Strip markdown code block if present
        text = raw.strip()
        if text.startswith("```"):
            # Remove ```json or ``` prefix and trailing ```
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error("llm_json_parse_failed", raw=raw[:500], error=str(e))
            raise ValueError(f"LLM returned invalid JSON: {e}") from e
