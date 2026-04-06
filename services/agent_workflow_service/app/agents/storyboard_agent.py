"""Storyboard Agent - generates storyboard with scenes and shots from script."""

from __future__ import annotations


class StoryboardAgent:
    """Agent responsible for generating storyboards.

    Input: ScriptDocument
    Output: StoryboardDocument with scenes and shot specs
    """

    async def run(self, project_id: int, script_version_id: str) -> dict:
        """Generate a storyboard from a script.

        TODO: Integrate with LLM gateway (Qwen) to:
        1. Break script sections into scenes
        2. Define shots per scene (type, camera, character, environment)
        3. Generate image_prompt and video_prompt for each shot
        4. Return StoryboardDocument
        """
        raise NotImplementedError("StoryboardAgent not yet implemented")
