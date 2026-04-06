"""MinIO object storage client with helper functions."""

from __future__ import annotations

import io
from datetime import timedelta

from minio import Minio

from packages.common.config import settings

_client: Minio | None = None


def get_minio() -> Minio:
    """Get or create the global MinIO client."""
    global _client
    if _client is None:
        _client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        # Ensure bucket exists
        if not _client.bucket_exists(settings.minio_bucket):
            _client.make_bucket(settings.minio_bucket)
    return _client


def reset_minio() -> None:
    """Reset the global MinIO client (useful in tests)."""
    global _client
    _client = None


def upload_bytes(
    object_key: str,
    data: bytes,
    content_type: str = "application/octet-stream",
    bucket: str | None = None,
) -> str:
    """Upload raw bytes to MinIO.

    Args:
        object_key: The key/path in the bucket (e.g. "projects/1/shots/abc/keyframe.png").
        data: Raw bytes to upload.
        content_type: MIME type of the data.
        bucket: Override bucket name (defaults to settings.minio_bucket).

    Returns:
        The object_key that was stored (same as input).
    """
    client = get_minio()
    target_bucket = bucket or settings.minio_bucket
    client.put_object(
        target_bucket,
        object_key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return object_key


def get_presigned_url(
    object_key: str,
    bucket: str | None = None,
    expires: timedelta | None = None,
) -> str:
    """Generate a presigned GET URL for an object.

    Args:
        object_key: The key/path in the bucket.
        bucket: Override bucket name (defaults to settings.minio_bucket).
        expires: URL expiry duration (default 1 hour).

    Returns:
        A presigned URL string.
    """
    client = get_minio()
    target_bucket = bucket or settings.minio_bucket
    return client.presigned_get_object(
        target_bucket,
        object_key,
        expires=expires or timedelta(hours=1),
    )


def delete_object(
    object_key: str,
    bucket: str | None = None,
) -> None:
    """Delete an object from MinIO.

    Args:
        object_key: The key/path in the bucket.
        bucket: Override bucket name (defaults to settings.minio_bucket).
    """
    client = get_minio()
    target_bucket = bucket or settings.minio_bucket
    client.remove_object(target_bucket, object_key)


def build_object_key(
    project_id: int,
    shot_id: str,
    asset_type: str,
    filename: str,
) -> str:
    """Build a standardized MinIO object key.

    Pattern: projects/{project_id}/shots/{shot_id}/{asset_type}/{filename}
    Example: projects/1/shots/abc123/keyframe/img_001.png
    """
    return f"projects/{project_id}/shots/{shot_id}/{asset_type}/{filename}"
