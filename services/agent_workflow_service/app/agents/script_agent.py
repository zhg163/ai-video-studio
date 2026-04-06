"""Script Agent - generates video script from creative brief."""

from __future__ import annotations


class ScriptAgent:
    """Agent responsible for generating video scripts.

    Input: CreativeBriefDocument
    Output: ScriptDocument with sections, narration, dialogue
    """

    async def run(self, project_id: int, brief_version_id: str) -> dict:
        """Generate a script from a confirmed brief.

        TODO: Integrate with LLM gateway (Qwen) to:
        1. Read brief constraints
        2. Generate section structure
        3. Write narration and dialogue per section
        4. Return ScriptDocument
        """
        raise NotImplementedError("ScriptAgent not yet implemented")
