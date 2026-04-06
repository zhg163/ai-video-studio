"""Character Agent - extracts and maintains character consistency."""

from __future__ import annotations


class CharacterAgent:
    """Agent responsible for character extraction and consistency.

    Input: StoryboardDocument
    Output: Character descriptions, reference images, consistency constraints
    """

    async def run(self, project_id: int, storyboard_version_id: str) -> dict:
        raise NotImplementedError("CharacterAgent not yet implemented")
