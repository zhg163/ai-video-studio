"""Common settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings. Loaded from env vars / .env file."""

    # App
    app_env: str = "development"
    debug: bool = True

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5433
    postgres_user: str = "ai_video"
    postgres_password: str = "changeme"
    postgres_db: str = "ai_video_studio"

    # MongoDB
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "ai_video_studio"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "ai-video-studio"
    minio_secure: bool = False

    # JWT
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # LLM
    qwen_api_key: str = ""
    qwen_model: str = "qwen-plus"

    # Image Gen
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_image_model: str = "gpt-image-1"

    # Video Gen
    kling_api_key: str = ""
    kling_access_key: str = ""
    kling_secret_key: str = ""
    kling_base_url: str = "https://api.klingai.com"

    # TTS
    qwen_tts_api_key: str = ""

    # Music
    minimax_api_key: str = ""

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_dsn_sync(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Singleton
settings = Settings()
