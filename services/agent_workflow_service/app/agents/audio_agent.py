"""Audio Agent - generates TTS voiceover and BGM."""

from __future__ import annotations


class AudioAgent:
    """Agent responsible for audio generation.

    Input: Shot voiceover text / project style
    Output: TTS audio files, BGM tracks
    """

    async def run(self, project_id: int, shot_id: str, audio_type: str = "tts") -> dict:
        raise NotImplementedError("AudioAgent not yet implemented")
