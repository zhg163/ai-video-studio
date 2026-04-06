"""Creative Agent - generates structured brief from user input.

Uses LLM to parse user intent and produce a structured CreativeBriefDocument.
"""

from __future__ import annotations

import structlog

from packages.domain.documents import BriefConstraints, SourceInput, StructuredBrief
from packages.model_gateways.llm_gateway import LLMGateway

logger = structlog.get_logger()

CREATIVE_BRIEF_SYSTEM_PROMPT = """你是一个专业的视频创意策划 AI 助手。根据用户的创意输入，生成结构化的创意简报（Creative Brief）。

输出一个 JSON 对象，包含以下字段：
{
  "structured_brief": {
    "goal": "视频的核心目标和主要信息",
    "audience": "目标受众描述",
    "duration_sec": 30,
    "aspect_ratio": "16:9",
    "language": "zh-CN",
    "style": "视频风格（如：温馨治愈、科技感、幽默搞笑、史诗大片等）",
    "platform": "目标发布平台（如：抖音、B站、YouTube、微信视频号等）"
  },
  "constraints": {
    "must_include": ["必须包含的元素列表"],
    "must_not": ["不能包含的元素列表"],
    "max_duration_sec": 60
  }
}

规则：
1. 如果用户没有明确指定某些字段，根据上下文合理推断
2. duration_sec 默认 30 秒，max_duration_sec 默认 60 秒
3. 所有字段都必须有值，不能为空字符串
4. must_include 至少包含 1 个元素
5. 回复纯 JSON，不要有任何额外文字"""


class CreativeAgent:
    """Agent responsible for generating creative briefs.

    Input: raw user text + reference assets
    Output: structured CreativeBriefDocument fields
    """

    def __init__(self, llm: LLMGateway) -> None:
        self.llm = llm

    async def run(
        self,
        project_id: int,
        user_input: str,
        references: list[str] | None = None,
    ) -> dict:
        """Generate a creative brief from user input.

        Returns a dict with keys: source_input, structured_brief, constraints
        """
        refs = references or []

        prompt = f"用户创意输入：\n{user_input}"
        if refs:
            prompt += f"\n\n参考素材：{', '.join(refs)}"

        logger.info("creative_agent_run", project_id=project_id, input_len=len(user_input))

        result = await self.llm.generate_json(
            prompt=prompt,
            system=CREATIVE_BRIEF_SYSTEM_PROMPT,
            temperature=0.7,
        )

        # Validate and normalize the response
        structured = StructuredBrief(**(result.get("structured_brief", {})))
        constraints = BriefConstraints(**(result.get("constraints", {})))

        return {
            "source_input": SourceInput(text=user_input, references=refs).model_dump(),
            "structured_brief": structured.model_dump(),
            "constraints": constraints.model_dump(),
        }
