"""Audio Generation Gateway (TTS + Music).

QwenTTSGateway uses DashScope's OpenAI-compatible /audio/speech endpoint.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import httpx

from packages.common.config import settings

logger = logging.getLogger(__name__)


class TTSGateway(ABC):
    """Abstract interface for text-to-speech."""

    @abstractmethod
    async def synthesize(self, text: str, voice: str = "default", **kwargs) -> bytes:
        """Synthesize speech from text. Returns audio bytes."""
        ...


class MusicGateway(ABC):
    """Abstract interface for music/BGM generation."""

    @abstractmethod
    async def generate(self, prompt: str, duration_sec: int = 30, **kwargs) -> bytes:
        """Generate background music. Returns audio bytes."""
        ...


class QwenTTSGateway(TTSGateway):
    """Qwen TTS implementation via DashScope OpenAI-compatible /audio/speech endpoint.

    API Reference:
        POST {base_url}/audio/speech
        Headers: Authorization: Bearer {api_key}
        Body: {"model": "qwen-tts", "input": "text", "voice": "alloy", "speed": 1.0}
        Response: raw audio bytes (content-type: audio/mpeg or audio/wav)
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or settings.qwen_tts_api_key
        self.base_url = (base_url or settings.qwen_tts_base_url).rstrip("/")
        self.model = model or settings.qwen_tts_model

    async def synthesize(
        self,
        text: str,
        voice: str = "default",
        *,
        speed: float = 1.0,
        response_format: str | None = None,
        **kwargs,
    ) -> bytes:
        """Synthesize speech from text using DashScope TTS.

        Args:
            text: The text to convert to speech.
            voice: Voice name (e.g. "alloy", "echo", "fable", etc.).
            speed: Playback speed (0.25 - 4.0, default 1.0).
            response_format: Audio format ("mp3" or "wav"). Defaults to settings.

        Returns:
            Raw audio bytes.

        Raises:
            httpx.HTTPStatusError: If the API returns a non-2xx status.
            ValueError: If API key is not configured.
        """
        if not self.api_key:
            raise ValueError("qwen_tts_api_key is not configured")

        if voice == "default":
            voice = settings.qwen_tts_voice

        fmt = response_format or settings.qwen_tts_response_format

        url = f"{self.base_url}/audio/speech"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": text,
            "voice": voice,
            "speed": speed,
            "response_format": fmt,
        }

        logger.info(
            "QwenTTS synthesize: model=%s voice=%s speed=%.1f format=%s text_len=%d",
            self.model,
            voice,
            speed,
            fmt,
            len(text),
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()

            audio_bytes = resp.content
            logger.info(
                "QwenTTS synthesize completed: %d bytes received", len(audio_bytes)
            )
            return audio_bytes


class MiniMaxMusicGateway(MusicGateway):
    """MiniMax Music implementation (placeholder)."""

    async def generate(self, prompt: str, duration_sec: int = 30, **kwargs) -> bytes:
        raise NotImplementedError("MiniMax Music integration not yet implemented")
