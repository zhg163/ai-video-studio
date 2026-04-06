"""MinIO object storage client."""

from __future__ import annotations

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
