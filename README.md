# VPAura - AI Chatbot Backend

AI Chatbot system providing streaming API responses using FastAPI, LangGraph, and PostgreSQL.

## Quick Start

```bash
docker-compose up -d postgres redis
uv sync
source .venv/bin/activate
alembic upgrade head
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

<http://localhost:8000/docs>

## Tech Stack

- FastAPI
- LangGraph
- SQLAlchemy + Alembic
- PostgreSQL
- Redis
