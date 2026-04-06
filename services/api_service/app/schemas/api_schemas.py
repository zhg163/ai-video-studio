"""API v1 request/response schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# --- Project Schemas ---

class ProjectCreate(BaseModel):
    name: str = Field(..., max_length=128)
    description: str | None = None
    aspect_ratio: str = "16:9"
    language: str = "zh-CN"


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, max_length=128)
    description: str | None = None
    aspect_ratio: str | None = None
    language: str | None = None


class ProjectOut(BaseModel):
    id: int
    tenant_id: int
    owner_id: int
    name: str
    description: str | None
    aspect_ratio: str
    language: str
    status: str
    current_brief_version_id: int | None
    current_script_version_id: int | None
    current_storyboard_version_id: int | None
    current_timeline_version_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Brief Schemas ---

class BriefGenerateRequest(BaseModel):
    text: str = Field(..., min_length=1)
    references: list[str] = []


class BriefOut(BaseModel):
    id: str
    project_id: int
    version_no: int
    source_input: dict
    structured_brief: dict
    constraints: dict
    created_by: int
    created_at: datetime | str


class BriefUpdate(BaseModel):
    """Partial update for a brief (structured_brief and/or constraints)."""
    structured_brief: dict | None = None
    constraints: dict | None = None


# --- Script Schemas ---

class ScriptGenerateRequest(BaseModel):
    brief_version_id: str


class ScriptOut(BaseModel):
    id: str
    project_id: int
    version_no: int
    brief_version_id: str
    title: str
    language: str
    sections: list[dict]
    full_text: str
    created_by: int
    created_at: datetime | str


class ScriptUpdate(BaseModel):
    """Partial update for a script."""
    title: str | None = None
    sections: list[dict] | None = None
    full_text: str | None = None


# --- Storyboard Schemas ---

class StoryboardGenerateRequest(BaseModel):
    script_version_id: str


class StoryboardOut(BaseModel):
    id: str
    project_id: int
    version_no: int
    script_version_id: str
    scenes: list[dict]
    created_at: datetime | str


class StoryboardUpdate(BaseModel):
    """Partial update for a storyboard (scenes can be edited)."""
    scenes: list[dict] | None = None


# --- Shot Schemas ---

class VideoInputMode(str, Enum):
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"


class GenerateImageRequest(BaseModel):
    """Request to generate keyframe image(s) for a shot."""
    image_model: str = "gpt-image-1"
    candidate_count: int = Field(default=1, ge=1, le=4)
    resolution: str = "1024x1024"
    reference_asset_ids: list[int] = []
    prompt_override: str | None = None  # Override the shot's image_prompt


class GenerateVideoRequest(BaseModel):
    """Request to generate video for a shot."""
    video_model: str = "kling-v1"
    input_mode: VideoInputMode = VideoInputMode.IMAGE_TO_VIDEO
    image_asset_id: int | None = None  # Required for image_to_video mode
    duration_sec: float = Field(default=5.0, ge=1.0, le=30.0)
    resolution: str = "1080p"
    prompt_override: str | None = None  # Override the shot's video_prompt


class ShotUpdate(BaseModel):
    """Partial update for a shot's editable fields."""
    image_prompt: str | None = None
    video_prompt: str | None = None
    character_desc: str | None = None
    environment_desc: str | None = None
    action_desc: str | None = None
    voiceover_text: str | None = None
    duration_sec: float | None = None
    shot_type: str | None = None
    camera_movement: str | None = None


class ShotOut(BaseModel):
    """Shot output (from storyboard's ShotSpec)."""
    shot_id: str
    scene_id: str
    order_no: int
    shot_type: str
    camera_movement: str
    character_desc: str
    environment_desc: str
    action_desc: str
    voiceover_text: str
    image_prompt: str
    video_prompt: str
    duration_sec: float
    status: str
    selected_asset_ids: list[int]


class AssetOut(BaseModel):
    """Asset file output."""
    id: int
    project_id: int
    asset_type: str
    usage_type: str
    mime_type: str | None
    file_name: str
    object_key: str
    file_size: int | None
    duration_ms: int | None
    width: int | None
    height: int | None
    status: str
    presigned_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class GenerationTaskOut(BaseModel):
    """Generation task output."""
    id: int
    project_id: int
    task_type: str
    biz_key: str | None
    model_provider: str | None
    model_name: str | None
    input_ref: dict | None
    output_ref: dict | None
    status: str
    retry_count: int
    error_code: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Timeline Schemas ---

class TimelineTrackType(str, Enum):
    VIDEO = "video"
    VOICEOVER = "voiceover"
    BGM = "bgm"
    SUBTITLE = "subtitle"


class TransitionType(str, Enum):
    FADE = "fade"
    DISSOLVE = "dissolve"
    CUT = "cut"
    WIPE = "wipe"


class TimelineClipOut(BaseModel):
    """A single clip on a timeline track."""
    clip_id: str
    source_shot_id: str = ""
    source_asset_id: int | None = None
    start_ms: int = 0
    end_ms: int = 0
    offset_ms: int = 0
    volume: float | None = None
    speed: float = 1.0


class TimelineTrackOut(BaseModel):
    """A single track in the timeline."""
    track_id: str
    track_type: str = "video"
    clips: list[TimelineClipOut] = []


class SubtitleSegmentOut(BaseModel):
    """A subtitle segment."""
    id: str
    start_ms: int
    end_ms: int
    text: str


class TransitionOut(BaseModel):
    """A transition between two clips."""
    id: str
    from_clip_id: str
    to_clip_id: str
    type: str = "fade"
    duration_ms: int = 300


class TimelineOut(BaseModel):
    """Timeline output (from MongoDB document)."""
    id: str
    project_id: int
    version_no: int
    storyboard_version_id: str
    tracks: list[TimelineTrackOut] = []
    subtitle_segments: list[SubtitleSegmentOut] = []
    transitions: list[TransitionOut] = []
    duration_ms: int = 0
    created_at: datetime | str


class AssembleTimelineRequest(BaseModel):
    """Request to auto-assemble a timeline from a storyboard."""
    storyboard_version_id: str
    voiceover_asset_id: int | None = None
    bgm_asset_id: int | None = None
    default_transition: TransitionType = TransitionType.CUT
    transition_duration_ms: int = Field(default=0, ge=0, le=2000)


class TimelineUpdate(BaseModel):
    """Partial update for a timeline."""
    tracks: list[dict] | None = None
    subtitle_segments: list[dict] | None = None
    transitions: list[dict] | None = None


class ClipReorderRequest(BaseModel):
    """Reorder clips within a track."""
    track_id: str
    clip_ids: list[str]  # Ordered list of clip IDs defining the new order


class ClipReplaceRequest(BaseModel):
    """Replace a clip's underlying asset."""
    track_id: str
    clip_id: str
    new_asset_id: int


# --- Audio / TTS Schemas ---


class VoiceGender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class GenerateVoiceoverRequest(BaseModel):
    """Request to batch-generate voiceover for all shots in a storyboard."""
    storyboard_version_id: str
    voice_name: str = "alloy"
    speed: float = Field(default=1.0, ge=0.25, le=4.0)


class GenerateVoiceoverForShotRequest(BaseModel):
    """Request to generate voiceover for a single shot."""
    voice_name: str = "alloy"
    speed: float = Field(default=1.0, ge=0.25, le=4.0)
    text_override: str | None = None  # Override shot's voiceover_text


class VoiceoverResultItem(BaseModel):
    """Result for a single shot's voiceover generation."""
    shot_id: str
    asset_id: int | None = None
    status: str  # "completed" | "failed" | "skipped"
    error: str | None = None


class BatchVoiceoverOut(BaseModel):
    """Response for batch voiceover generation."""
    project_id: int
    storyboard_version_id: str
    results: list[VoiceoverResultItem]
    total: int
    completed: int
    failed: int
    skipped: int


# --- Render / Export Schemas ---


class RenderResolution(str, Enum):
    P720 = "720p"
    P1080 = "1080p"
    K2 = "2k"
    K4 = "4k"


class RenderFormat(str, Enum):
    MP4 = "mp4"
    MOV = "mov"


class RenderStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"


class CreateRenderRequest(BaseModel):
    """Request to create a render/export task."""
    timeline_version_id: str
    resolution: RenderResolution = RenderResolution.P1080
    burn_subtitle: bool = True
    format: RenderFormat = RenderFormat.MP4


class RenderTaskOut(BaseModel):
    """Render task output."""
    id: int
    project_id: int
    timeline_version_id: int | None
    output_asset_id: int | None
    render_profile: str
    status: str
    progress: int
    error_message: str | None
    created_by: int
    created_at: datetime
    updated_at: datetime
    output_url: str | None = None
    cover_url: str | None = None

    model_config = {"from_attributes": True}
