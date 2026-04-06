"""Editing Agent - assembles timeline from generated assets."""

from __future__ import annotations


class EditingAgent:
    """Agent responsible for timeline assembly.

    Input: StoryboardDocument + generated assets
    Output: TimelineDocument with tracks, clips, transitions
    """

    async def run(self, project_id: int, storyboard_version_id: str) -> dict:
        raise NotImplementedError("EditingAgent not yet implemented")
