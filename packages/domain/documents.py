"""MongoDB document schemas as Pydantic models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# --- Creative Brief ---

class SourceInput(BaseModel):
    text: str = ""
    references: list[str] = []


class StructuredBrief(BaseModel):
    goal: str = ""
    audience: str = ""
    duration_sec: int = 30
    aspect_ratio: str = "16:9"
    language: str = "zh-CN"
    style: str = ""
    platform: str = ""


class BriefConstraints(BaseModel):
    must_include: list[str] = []
    must_not: list[str] = []
    max_duration_sec: int = 60


class CreativeBriefDocument(BaseModel):
    id: str = Field(alias="_id", default="")
    project_id: int
    version_no: int = 1
    source_input: SourceInput = SourceInput()
    structured_brief: StructuredBrief = StructuredBrief()
    constraints: BriefConstraints = BriefConstraints()
    created_by: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}


# --- Script ---

class ScriptSection(BaseModel):
    section_no: int
    title: str = ""
    narration: str = ""
    dialogue: list[str] = []
    subtitle: str = ""


class ScriptDocument(BaseModel):
    id: str = Field(alias="_id", default="")
    project_id: int
    version_no: int = 1
    brief_version_id: str = ""
    title: str = ""
    language: str = "zh-CN"
    sections: list[ScriptSection] = []
    full_text: str = ""
    created_by: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}


# --- Storyboard ---

class ShotSpec(BaseModel):
    shot_id: str
    order_no: int
    shot_type: str = "wide"  # wide/medium/close/extreme_close/pov
    camera_movement: str = "static"  # static/push_in/pull_out/pan/tilt/dolly
    character_desc: str = ""
    environment_desc: str = ""
    action_desc: str = ""
    voiceover_text: str = ""
    image_prompt: str = ""
    video_prompt: str = ""
    duration_sec: float = 4.0
    status: str = "pending"
    selected_asset_ids: list[int] = []


class SceneSpec(BaseModel):
    scene_id: str
    title: str = ""
    summary: str = ""
    estimated_duration_sec: float = 8.0
    shots: list[ShotSpec] = []


class StoryboardDocument(BaseModel):
    id: str = Field(alias="_id", default="")
    project_id: int
    version_no: int = 1
    script_version_id: str = ""
    scenes: list[SceneSpec] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}


# --- Timeline ---

class TimelineClip(BaseModel):
    clip_id: str
    source_asset_id: int | None = None
    source_shot_id: str = ""
    start_ms: int = 0
    end_ms: int = 0
    offset_ms: int = 0
    volume: float | None = None
    speed: float = 1.0


class TimelineTrack(BaseModel):
    track_id: str
    track_type: str = "video"  # video/audio/bgm/voiceover
    clips: list[TimelineClip] = []


class SubtitleSegment(BaseModel):
    id: str
    start_ms: int
    end_ms: int
    text: str


class Transition(BaseModel):
    id: str
    from_clip_id: str
    to_clip_id: str
    type: str = "fade"  # fade/dissolve/cut/wipe
    duration_ms: int = 300


class TimelineDocument(BaseModel):
    id: str = Field(alias="_id", default="")
    project_id: int
    version_no: int = 1
    storyboard_version_id: str = ""
    tracks: list[TimelineTrack] = []
    subtitle_segments: list[SubtitleSegment] = []
    transitions: list[Transition] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}


# --- Agent Run ---

class AgentRunDocument(BaseModel):
    id: str = Field(alias="_id", default="")
    project_id: int
    workflow_instance_id: str = ""
    agent_name: str = ""
    input_ref: dict = {}
    output_ref: dict = {}
    status: str = "running"  # running/success/failed
    latency_ms: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}
