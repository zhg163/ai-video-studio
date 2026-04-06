"""Creative Agent - generates structured brief from user input."""

from __future__ import annotations


class CreativeAgent:
    """Agent responsible for generating creative briefs.

    Input: raw user text + reference assets
    Output: structured CreativeBriefDocument
    """

    async def run(self, project_id: int, user_input: str, references: list[str] | None = None) -> dict:
        """Generate a creative brief from user input.

        TODO: Integrate with LLM gateway (Qwen) to:
        1. Parse user intent
        2. Extract structured fields (goal, audience, style, platform)
        3. Generate constraints
        4. Return CreativeBriefDocument
        """
        raise NotImplementedError("CreativeAgent not yet implemented")
