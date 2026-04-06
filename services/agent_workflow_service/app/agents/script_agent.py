"""Script Agent - generates structured script from a confirmed brief.

Uses LLM to convert a creative brief into a multi-section video script.
"""

from __future__ import annotations

import structlog

from packages.domain.documents import ScriptSection
from packages.model_gateways.llm_gateway import LLMGateway

logger = structlog.get_logger()

SCRIPT_SYSTEM_PROMPT = """你是一个专业的视频脚本撰写 AI 助手。根据提供的创意简报（Creative Brief），生成一个结构化的视频脚本。

输出一个 JSON 对象，包含以下字段：
{
  "title": "视频标题",
  "language": "zh-CN",
  "sections": [
    {
      "section_no": 1,
      "title": "段落标题（如：开场）",
      "narration": "旁白/解说词",
      "dialogue": ["对话1", "对话2"],
      "subtitle": "字幕文本"
    }
  ],
  "full_text": "完整的脚本文本（合并所有段落的旁白和对话）"
}

规则：
1. 根据 brief 中的 duration_sec 合理分配段落数（每 10 秒约 1 个段落）
2. 每个段落的 narration 不超过 50 字（约 10 秒语速）
3. sections 至少包含 2 个段落（开场 + 结尾）
4. full_text 是所有 narration 和 dialogue 的拼接，用换行分隔
5. 风格要与 brief 中的 style 一致
6. 语言要与 brief 中的 language 一致
7. 回复纯 JSON，不要有任何额外文字"""


class ScriptAgent:
    """Agent responsible for generating video scripts from briefs.

    Input: creative brief data (structured_brief + constraints)
    Output: structured ScriptDocument fields
    """

    def __init__(self, llm: LLMGateway) -> None:
        self.llm = llm

    async def run(
        self,
        project_id: int,
        brief_data: dict,
        language: str = "zh-CN",
    ) -> dict:
        """Generate a video script from a creative brief.

        Args:
            project_id: The project ID.
            brief_data: Dict with keys: structured_brief, constraints, source_input.
            language: Target language for the script.

        Returns:
            Dict with keys: title, language, sections, full_text
        """
        structured_brief = brief_data.get("structured_brief", {})
        constraints = brief_data.get("constraints", {})

        prompt = f"""创意简报：
- 目标：{structured_brief.get('goal', '未指定')}
- 受众：{structured_brief.get('audience', '未指定')}
- 时长：{structured_brief.get('duration_sec', 30)} 秒
- 画面比例：{structured_brief.get('aspect_ratio', '16:9')}
- 语言：{structured_brief.get('language', language)}
- 风格：{structured_brief.get('style', '未指定')}
- 平台：{structured_brief.get('platform', '未指定')}

约束：
- 必须包含：{', '.join(constraints.get('must_include', []))}
- 不能包含：{', '.join(constraints.get('must_not', []))}
- 最大时长：{constraints.get('max_duration_sec', 60)} 秒

请根据以上创意简报生成一个完整的视频脚本。"""

        logger.info("script_agent_run", project_id=project_id)

        result = await self.llm.generate_json(
            prompt=prompt,
            system=SCRIPT_SYSTEM_PROMPT,
            temperature=0.7,
        )

        # Validate and normalize sections
        raw_sections = result.get("sections", [])
        sections = []
        for i, sec in enumerate(raw_sections):
            section = ScriptSection(
                section_no=sec.get("section_no", i + 1),
                title=sec.get("title", f"段落 {i + 1}"),
                narration=sec.get("narration", ""),
                dialogue=sec.get("dialogue", []),
                subtitle=sec.get("subtitle", ""),
            )
            sections.append(section.model_dump())

        # Build full_text if not provided
        full_text = result.get("full_text", "")
        if not full_text:
            parts = []
            for sec in sections:
                if sec["narration"]:
                    parts.append(sec["narration"])
                for d in sec["dialogue"]:
                    parts.append(d)
            full_text = "\n".join(parts)

        return {
            "title": result.get("title", "未命名脚本"),
            "language": result.get("language", language),
            "sections": sections,
            "full_text": full_text,
        }
