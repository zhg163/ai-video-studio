"""API v1 request/response schemas."""

from __future__ import annotations

from datetime import datetime

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
