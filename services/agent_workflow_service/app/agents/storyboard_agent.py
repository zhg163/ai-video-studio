"""Storyboard Agent - generates storyboard with scenes and shots from script.

Uses LLM to convert a script into visual scenes with shot specifications.
"""

from __future__ import annotations

import uuid

import structlog

from packages.domain.documents import SceneSpec, ShotSpec
from packages.model_gateways.llm_gateway import LLMGateway

logger = structlog.get_logger()

STORYBOARD_SYSTEM_PROMPT = """你是一个专业的视频分镜策划 AI 助手。根据提供的视频脚本，生成一个详细的分镜脚本（Storyboard）。

输出一个 JSON 对象，包含以下字段：
{
  "scenes": [
    {
      "scene_id": "scene_001",
      "title": "场景标题",
      "summary": "场景概述",
      "estimated_duration_sec": 10.0,
      "shots": [
        {
          "shot_id": "shot_001",
          "order_no": 1,
          "shot_type": "wide",
          "camera_movement": "static",
          "character_desc": "人物描述（如果有）",
          "environment_desc": "环境描述",
          "action_desc": "动作/发生的事情",
          "voiceover_text": "对应的旁白文本",
          "image_prompt": "用于生成关键帧图片的英文 prompt",
          "video_prompt": "用于生成视频片段的英文 prompt",
          "duration_sec": 4.0
        }
      ]
    }
  ]
}

规则：
1. 每个脚本段落（section）对应一个场景（scene）
2. 每个场景包含 1-3 个镜头（shot）
3. shot_type 可选值：wide（远景）、medium（中景）、close（近景）、extreme_close（特写）、pov（第一人称）
4. camera_movement 可选值：static（静止）、push_in（推进）、pull_out（拉远）、pan（平移）、tilt（俯仰）、dolly（轨道移动）
5. image_prompt 和 video_prompt 必须是英文，要详细描述视觉内容
6. 每个 shot 的 duration_sec 在 2-6 秒之间
7. 所有 shot 的总时长应接近脚本指定的目标时长
8. scene_id 格式为 scene_001、scene_002 等
9. shot_id 格式为 shot_001、shot_002 等（全局递增）
10. 回复纯 JSON，不要有任何额外文字"""


class StoryboardAgent:
    """Agent responsible for generating storyboards.

    Input: ScriptDocument data (sections, title, language)
    Output: StoryboardDocument with scenes and shot specs
    """

    def __init__(self, llm: LLMGateway) -> None:
        self.llm = llm

    async def run(
        self,
        project_id: int,
        script_data: dict,
        target_duration_sec: int = 30,
    ) -> dict:
        """Generate a storyboard from a script.

        Args:
            project_id: The project ID.
            script_data: Dict with keys: title, sections, full_text, language.
            target_duration_sec: Target video duration.

        Returns:
            Dict with key: scenes (list of scene dicts with nested shots).
        """
        sections = script_data.get("sections", [])
        title = script_data.get("title", "")

        # Build section summaries for the prompt
        section_text = ""
        for sec in sections:
            section_text += f"\n段落 {sec.get('section_no', '?')} - {sec.get('title', '')}:\n"
            section_text += f"  旁白: {sec.get('narration', '')}\n"
            if sec.get("dialogue"):
                section_text += f"  对话: {'; '.join(sec['dialogue'])}\n"

        prompt = f"""视频标题：{title}
目标时长：{target_duration_sec} 秒

脚本内容：
{section_text}

请根据以上脚本生成详细的分镜脚本。"""

        logger.info("storyboard_agent_run", project_id=project_id, sections=len(sections))

        result = await self.llm.generate_json(
            prompt=prompt,
            system=STORYBOARD_SYSTEM_PROMPT,
            temperature=0.7,
        )

        # Validate and normalize scenes
        raw_scenes = result.get("scenes", [])
        scenes = []
        global_shot_no = 0
        for i, raw_scene in enumerate(raw_scenes):
            shots = []
            for j, raw_shot in enumerate(raw_scene.get("shots", [])):
                global_shot_no += 1
                shot = ShotSpec(
                    shot_id=raw_shot.get("shot_id", f"shot_{global_shot_no:03d}"),
                    order_no=global_shot_no,
                    shot_type=raw_shot.get("shot_type", "wide"),
                    camera_movement=raw_shot.get("camera_movement", "static"),
                    character_desc=raw_shot.get("character_desc", ""),
                    environment_desc=raw_shot.get("environment_desc", ""),
                    action_desc=raw_shot.get("action_desc", ""),
                    voiceover_text=raw_shot.get("voiceover_text", ""),
                    image_prompt=raw_shot.get("image_prompt", ""),
                    video_prompt=raw_shot.get("video_prompt", ""),
                    duration_sec=raw_shot.get("duration_sec", 4.0),
                    status="pending",
                )
                shots.append(shot.model_dump())

            scene = SceneSpec(
                scene_id=raw_scene.get("scene_id", f"scene_{i + 1:03d}"),
                title=raw_scene.get("title", f"场景 {i + 1}"),
                summary=raw_scene.get("summary", ""),
                estimated_duration_sec=raw_scene.get("estimated_duration_sec", 8.0),
                shots=shots,
            )
            scenes.append(scene.model_dump())

        return {"scenes": scenes}
