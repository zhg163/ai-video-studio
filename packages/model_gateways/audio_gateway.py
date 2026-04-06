"""Audio Generation Gateway (TTS + Music)."""

from __future__ import annotations

from abc import ABC, abstractmethod


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
    """Qwen TTS implementation (placeholder)."""

    async def synthesize(self, text: str, voice: str = "default", **kwargs) -> bytes:
        raise NotImplementedError("Qwen TTS integration not yet implemented")


class MiniMaxMusicGateway(MusicGateway):
    """MiniMax Music implementation (placeholder)."""

    async def generate(self, prompt: str, duration_sec: int = 30, **kwargs) -> bytes:
        raise NotImplementedError("MiniMax Music integration not yet implemented")
