"""Image Generation Gateway.

GPT Image 1 implementation uses the OpenAI Images API.
Returns raw image bytes; callers are responsible for storing to MinIO.
"""

from __future__ import annotations

import base64
from abc import ABC, abstractmethod

import httpx
import structlog

from packages.common.config import settings

logger = structlog.get_logger()


class ImageGateway(ABC):
    """Abstract interface for image generation."""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> list[bytes]:
        """Generate image(s) from a prompt. Returns a list of image bytes."""
        ...


class GPTImageGateway(ImageGateway):
    """GPT Image 1 implementation via OpenAI Images API.

    Uses POST /v1/images/generations with response_format=b64_json
    to avoid expiring URLs. Returns raw PNG/WebP bytes.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.openai_api_key
        self.base_url = (base_url or settings.openai_base_url).rstrip("/")
        self.model = model or settings.openai_image_model
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for GPTImageGateway")

    async def generate(self, prompt: str, **kwargs) -> list[bytes]:
        """Generate image(s) using GPT Image 1.

        Keyword args:
            n: Number of images to generate (default 1, max 4).
            size: Image size, e.g. "1024x1024", "1536x1024", "1024x1536".
            quality: "auto", "high", "medium", "low" (default "auto").
        """
        n = kwargs.get("n", 1)
        size = kwargs.get("size", "1024x1024")
        quality = kwargs.get("quality", "auto")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": n,
            "size": size,
            "quality": quality,
        }

        logger.info(
            "gpt_image_generate_start",
            model=self.model,
            prompt_len=len(prompt),
            n=n,
            size=size,
        )

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/images/generations",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        images: list[bytes] = []
        for item in data.get("data", []):
            if "b64_json" in item:
                images.append(base64.b64decode(item["b64_json"]))
            elif "url" in item:
                # Fallback: download from URL
                async with httpx.AsyncClient(timeout=60.0) as dl_client:
                    dl_resp = await dl_client.get(item["url"])
                    dl_resp.raise_for_status()
                    images.append(dl_resp.content)

        logger.info(
            "gpt_image_generate_done",
            model=self.model,
            count=len(images),
            total_bytes=sum(len(img) for img in images),
        )
        return images


class FluxImageGateway(ImageGateway):
    """FLUX API implementation (placeholder for backup)."""

    async def generate(self, prompt: str, **kwargs) -> list[bytes]:
        raise NotImplementedError("FLUX Image integration not yet implemented")
