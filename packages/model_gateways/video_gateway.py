"""Video Generation Gateway.

Kling 3.0 implementation uses the Kling AI API.
Kling is an async API: submit task -> poll status -> download video.
Authentication uses access_key + secret_key to sign a JWT token.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from enum import Enum

import httpx
import jwt
import structlog

from packages.common.config import settings

logger = structlog.get_logger()


class VideoInputMode(str, Enum):
    """Video generation input modes."""
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"


class VideoTaskStatus(str, Enum):
    """Possible statuses from the Kling API."""
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    SUCCEED = "succeed"
    FAILED = "failed"


class VideoTaskResult:
    """Result of a video generation task query."""

    def __init__(
        self,
        task_id: str,
        status: str,
        video_url: str | None = None,
        duration_sec: float | None = None,
        error_message: str | None = None,
    ):
        self.task_id = task_id
        self.status = status
        self.video_url = video_url
        self.duration_sec = duration_sec
        self.error_message = error_message


class VideoGateway(ABC):
    """Abstract interface for video generation."""

    @abstractmethod
    async def submit_task(
        self,
        prompt: str,
        *,
        mode: VideoInputMode = VideoInputMode.TEXT_TO_VIDEO,
        image_url: str | None = None,
        duration_sec: float = 5.0,
        aspect_ratio: str = "16:9",
        **kwargs,
    ) -> str:
        """Submit a video generation task. Returns the external task_id."""
        ...

    @abstractmethod
    async def query_task(self, task_id: str) -> VideoTaskResult:
        """Query the status of a submitted task."""
        ...

    async def download_video(self, video_url: str) -> bytes:
        """Download video bytes from a URL."""
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.get(video_url)
            resp.raise_for_status()
            return resp.content


class KlingVideoGateway(VideoGateway):
    """Kling 3.0 video generation implementation.

    Authentication: JWT signed with access_key (header.iss) and secret_key (HMAC).
    API flow:
      1. POST /v1/videos/text2video or /v1/videos/image2video -> task_id
      2. GET  /v1/videos/text2video/{task_id} -> status + video_url
    """

    def __init__(
        self,
        access_key: str | None = None,
        secret_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.access_key = access_key or settings.kling_access_key
        self.secret_key = secret_key or settings.kling_secret_key
        self.base_url = (base_url or settings.kling_base_url).rstrip("/")
        if not self.access_key or not self.secret_key:
            raise ValueError(
                "KLING_ACCESS_KEY and KLING_SECRET_KEY are required for KlingVideoGateway"
            )

    def _generate_jwt_token(self) -> str:
        """Generate a JWT token for Kling API authentication.

        The token is signed with HS256 using the secret_key.
        The payload includes iss (access_key), exp, and nbf claims.
        """
        now = int(time.time())
        headers = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "iss": self.access_key,
            "exp": now + 1800,  # 30 min expiry
            "nbf": now - 5,  # allow 5 sec clock skew
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256", headers=headers)

    def _get_headers(self) -> dict[str, str]:
        """Build request headers with JWT auth."""
        token = self._generate_jwt_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def submit_task(
        self,
        prompt: str,
        *,
        mode: VideoInputMode = VideoInputMode.TEXT_TO_VIDEO,
        image_url: str | None = None,
        duration_sec: float = 5.0,
        aspect_ratio: str = "16:9",
        **kwargs,
    ) -> str:
        """Submit a video generation task to Kling API.

        Returns the external task_id from Kling.
        """
        model_name = kwargs.get("model_name", "kling-v1")

        if mode == VideoInputMode.IMAGE_TO_VIDEO:
            endpoint = f"{self.base_url}/v1/videos/image2video"
            payload: dict = {
                "model_name": model_name,
                "prompt": prompt,
                "image": image_url,
                "duration": str(duration_sec),
                "aspect_ratio": aspect_ratio,
            }
            # Add optional tail_image for start-end frame mode
            tail_image = kwargs.get("tail_image")
            if tail_image:
                payload["tail_image"] = tail_image
        else:
            endpoint = f"{self.base_url}/v1/videos/text2video"
            payload = {
                "model_name": model_name,
                "prompt": prompt,
                "duration": str(duration_sec),
                "aspect_ratio": aspect_ratio,
            }

        # Optional: negative prompt, cfg_scale, seed
        if kwargs.get("negative_prompt"):
            payload["negative_prompt"] = kwargs["negative_prompt"]
        if kwargs.get("cfg_scale"):
            payload["cfg_scale"] = kwargs["cfg_scale"]

        logger.info(
            "kling_submit_task",
            mode=mode.value,
            model=model_name,
            prompt_len=len(prompt),
            duration=duration_sec,
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                headers=self._get_headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        # Kling API returns { "code": 0, "data": { "task_id": "..." } }
        task_id = data["data"]["task_id"]
        logger.info("kling_task_submitted", task_id=task_id)
        return task_id

    async def query_task(self, task_id: str) -> VideoTaskResult:
        """Query the status of a Kling video generation task."""
        # Kling uses the same endpoint pattern for both text2video and image2video queries
        endpoint = f"{self.base_url}/v1/videos/text2video/{task_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                endpoint,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            data = response.json()

        task_data = data.get("data", {})
        status = task_data.get("task_status", "processing")

        video_url = None
        duration = None
        error_msg = None

        if status == "succeed":
            works = task_data.get("task_result", {}).get("videos", [])
            if works:
                video_url = works[0].get("url")
                duration = works[0].get("duration")
        elif status == "failed":
            error_msg = task_data.get("task_status_msg", "Unknown error")

        logger.info(
            "kling_query_task",
            task_id=task_id,
            status=status,
            has_video=video_url is not None,
        )

        return VideoTaskResult(
            task_id=task_id,
            status=status,
            video_url=video_url,
            duration_sec=duration,
            error_message=error_msg,
        )
