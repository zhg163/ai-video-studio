"""Visual Agent - generates keyframe images and videos for shots."""

from __future__ import annotations


class VisualAgent:
    """Agent responsible for visual media generation.

    Input: ShotSpec with image_prompt/video_prompt
    Output: Generated keyframe images and video clips
    """

    async def run(self, project_id: int, shot_id: str, generation_type: str = "image") -> dict:
        raise NotImplementedError("VisualAgent not yet implemented")
