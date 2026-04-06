"""Review Agent - AI-powered quality review of generated content."""

from __future__ import annotations


class ReviewAgent:
    """Agent responsible for automated quality review.

    Input: Generated content (brief/script/storyboard/video)
    Output: Review comments, quality scores, improvement suggestions
    """

    async def run(self, project_id: int, target_type: str, target_id: str) -> dict:
        raise NotImplementedError("ReviewAgent not yet implemented")
