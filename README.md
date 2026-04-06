# AI Video Studio

AI Multi-Agent Video Production Platform (AI 多智能体视频制作平台)

## Overview

AI Video Studio is an AI-powered video production platform that orchestrates multiple AI agents to handle the complete video creation pipeline: from creative brief to final export.

**Core Pipeline:** `Creative Input → Brief → Script → Storyboard → Shot Generation → Audio/Subtitles → Timeline → Export`

## Architecture

- **api-service** - REST API gateway
- **agent-workflow-service** - AI agent orchestration & workflow state machine
- **media-render-service** - Asset management, timeline assembly, FFmpeg export
- **admin-service** - Model config, quotas, audit

## Tech Stack

- **Backend:** Python, FastAPI, Pydantic v2
- **Databases:** PostgreSQL, MongoDB, Redis
- **Storage:** MinIO
- **AI Orchestration:** LangGraph
- **Rendering:** FFmpeg
- **Frontend:** Vue 3 + TypeScript (planned)

## Development

```bash
# Create virtual environment
uv venv .venv --python python3.11
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"

# Start infrastructure
docker compose up -d

# Run tests
pytest

# Start api-service
uvicorn services.api-service.app.main:app --reload --port 8000
```

## License

MIT
