"""MongoDB async client using Motor."""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from packages.common.config import settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    """Get or create the global MongoDB client."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongo_uri)
    return _client


def get_mongo_db() -> AsyncIOMotorDatabase:
    """Get the application MongoDB database."""
    global _db
    if _db is None:
        _db = get_mongo_client()[settings.mongo_db]
    return _db


def reset_mongo() -> None:
    """Reset the global MongoDB client/db references.

    Used by tests to ensure the Motor client is bound to the current event loop.
    """
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None


async def close_mongo() -> None:
    """Close the MongoDB client connection."""
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None


# Collection name constants
class Collections:
    CREATIVE_BRIEF = "creative_brief"
    SCRIPT = "script"
    STORYBOARD = "storyboard"
    TIMELINE = "timeline"
    AGENT_RUN = "agent_run"
