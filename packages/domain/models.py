"""PostgreSQL ORM models for the core domain."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from packages.common.database import Base


class Tenant(Base):
    __tablename__ = "tenant"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    plan_type: Mapped[str] = mapped_column(String(32), default="free")
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class UserAccount(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    email: Mapped[str] = mapped_column(String(128), nullable=False)
    mobile: Mapped[str | None] = mapped_column(String(32), nullable=True)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="editor")  # owner/admin/editor/viewer
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Project(Base):
    __tablename__ = "project"
    __table_args__ = (
        Index("ix_project_tenant_owner_status", "tenant_id", "owner_id", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    aspect_ratio: Mapped[str] = mapped_column(String(16), default="16:9")
    language: Mapped[str] = mapped_column(String(16), default="zh-CN")
    status: Mapped[str] = mapped_column(String(32), default="draft")
    current_brief_version_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    current_script_version_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    current_storyboard_version_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    current_timeline_version_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProjectMember(Base):
    __tablename__ = "project_member"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="editor")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProjectVersion(Base):
    __tablename__ = "project_version"
    __table_args__ = (
        Index("ix_project_version_lookup", "project_id", "version_type", "version_no"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    version_type: Mapped[str] = mapped_column(String(32), nullable=False)  # brief/script/storyboard/timeline
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)  # MongoDB doc ID
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AssetFile(Base):
    __tablename__ = "asset_file"
    __table_args__ = (
        Index("ix_asset_file_project_type", "project_id", "asset_type", "usage_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)  # image/video/audio/subtitle/file
    usage_type: Mapped[str] = mapped_column(String(32), nullable=False)  # reference/keyframe/shot_video/tts/bgm/export
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    object_key: Mapped[str] = mapped_column(String(255), nullable=False)  # MinIO key
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GenerationTask(Base):
    __tablename__ = "generation_task"
    __table_args__ = (
        Index("ix_gen_task_project_type", "project_id", "task_type", "status"),
        Index("ix_gen_task_biz_key", "biz_key"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    task_type: Mapped[str] = mapped_column(String(32), nullable=False)
    biz_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    input_ref: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_ref: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    cost_amount: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RenderTask(Base):
    __tablename__ = "render_task"
    __table_args__ = (
        Index("ix_render_task_project_status", "project_id", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    timeline_version_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    output_asset_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    render_profile: Mapped[str] = mapped_column(String(64), default="1080p")
    status: Mapped[str] = mapped_column(String(32), default="queued")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ReviewComment(Base):
    __tablename__ = "review_comment"
    __table_args__ = (
        Index("ix_review_comment_target", "project_id", "target_type", "target_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_tenant_time", "tenant_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(64), nullable=False)
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
