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
