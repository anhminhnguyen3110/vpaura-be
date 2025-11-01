# VPAura - AI Chatbot Project Plan

## 📋 Project Overview

**Project Name:** VPAura  
**Description:** AI Chatbot system providing streaming API responses  
**Tech Stack:**
- FastAPI (API Framework)
- LangGraph (AI/LLM Orchestration)
- SQLAlchemy + Alembic (Database ORM & Migrations)
- pyproject.toml (Dependency Management)

---

## 🎯 System Design - C4 Model

### Level 1: Context Diagram (High-Level)

```
┌─────────────────────────────────────────────────────────────┐
│                     System Context                           │
│                                                              │
│  ┌──────────┐          ┌──────────────┐        ┌─────────┐ │
│  │  Client  │──HTTP──▶ │   VPAura     │──API──▶│   LLM   │ │
│  │   Apps   │◀────────│   Chatbot    │◀───────│Provider │ │
│  └──────────┘          │    System    │        └─────────┘ │
│                        └──────┬───────┘                     │
│                               │                             │
│                               ▼                             │
│                        ┌──────────────┐                     │
│                        │   Database   │                     │
│                        │ (PostgreSQL) │                     │
│                        └──────────────┘                     │
└─────────────────────────────────────────────────────────────┘

Key Interactions:
- Client Apps: Web/Mobile applications consuming the chatbot API
- VPAura System: Core chatbot service with streaming capabilities
- LLM Provider: External AI service (OpenAI, Anthropic, etc.)
- Database: Persistent storage for conversations, users, configs
```

### Level 2: Container Diagram (Architecture)

```
┌────────────────────────────────────────────────────────────────────────┐
│                         VPAura System                                   │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                    API Layer (FastAPI)                            │ │
│  │  ┌──────────────────┐          ┌──────────────────┐              │ │
│  │  │   REST API       │          │  Streaming API   │              │ │
│  │  │   Endpoints      │          │  (SSE Handler)   │              │ │
│  │  └────────┬─────────┘          └────────┬─────────┘              │ │
│  └───────────┼────────────────────────────┼────────────────────────┘ │
│              │                            │                           │
│  ┌───────────┼────────────────────────────┼────────────────────────┐ │
│  │           ▼                            ▼                        │ │
│  │                  Middleware Layer                               │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │ │
│  │  │ Rate Limiter │  │   Logging    │  │   Metrics    │         │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │ │
│  │  ┌──────────────┐  ┌──────────────┐                           │ │
│  │  │     Auth     │  │     CORS     │                           │ │
│  │  └──────────────┘  └──────────────┘                           │ │
│  └───────────────────────────┬──────────────────────────────────┘ │
│                              │                                     │
│  ┌───────────────────────────┼──────────────────────────────────┐ │
│  │                           ▼                                  │ │
│  │              Service Layer (Business Logic)                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │ │
│  │  │   Chatbot    │  │ Conversation │  │     User     │      │ │
│  │  │   Service    │  │   Service    │  │   Service    │      │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │ │
│  └─────────┼──────────────────┼──────────────────┼──────────────┘ │
│            │                  │                  │                 │
│  ┌─────────┼──────────────────┼──────────────────┼──────────────┐ │
│  │         ▼                  │                  │              │ │
│  │    LangGraph Execution Engine                │              │ │
│  │  ┌────────────────────────────────┐          │              │ │
│  │  │      Graph Builder             │          │              │ │
│  │  │  ┌──────────┐  ┌────────────┐ │          │              │ │
│  │  │  │  Nodes   │  │   Edges    │ │          │              │ │
│  │  │  │ (LLM,    │  │(Conditions)│ │          │              │ │
│  │  │  │ Context, │  │            │ │          │              │ │
│  │  │  │ Response)│  │            │ │          │              │ │
│  │  │  └──────────┘  └────────────┘ │          │              │ │
│  │  │      State Management          │          │              │ │
│  │  └────────────────────────────────┘          │              │ │
│  └─────────────────────────────────────────────┼──────────────┘ │
│                                                 │                 │
│  ┌──────────────────────────────────────────────┼──────────────┐ │
│  │         Repository Layer (Data Access)       ▼              │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │ │
│  │  │ Conversation │  │     User     │  │   Message    │     │ │
│  │  │  Repository  │  │  Repository  │  │  Repository  │     │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │ │
│  └─────────┼──────────────────┼──────────────────┼──────────────┘ │
│            │                  │                  │                 │
│  ┌─────────┼──────────────────┼──────────────────┼──────────────┐ │
│  │         ▼                  ▼                  ▼              │ │
│  │           Database Connection Pool (Async)                  │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │        SQLAlchemy Async Engine & Session Factory       │ │ │
│  │  └────────────────────┬───────────────────────────────────┘ │ │
│  └───────────────────────┼──────────────────────────────────────┘ │
│                          │                                         │
│  ┌───────────────────────┼──────────────────────────────────────┐ │
│  │                       ▼                                      │ │
│  │              PostgreSQL Database                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │ │
│  │  │    Tables    │  │   Indexes    │  │    Alembic   │      │ │
│  │  │  (ORM Models)│  │              │  │  Migrations  │      │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                  Redis Cache Layer                           │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │ │
│  │  │ Rate Limit   │  │ Conversation │  │   Session    │      │ │
│  │  │    State     │  │   Context    │  │    Cache     │      │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  External Dependencies:                                             │
│  ┌──────────────┐          ┌──────────────┐                       │
│  │ LLM Provider │          │  Monitoring  │                       │
│  │  (OpenAI)    │          │ (Prometheus) │                       │
│  └──────────────┘          └──────────────┘                       │
└────────────────────────────────────────────────────────────────────┘

Key Changes:
✅ Added Middleware Layer (Rate Limiter, Logging, Metrics, Auth, CORS)
✅ Removed WebSocket Handler (SSE only for streaming)
✅ Added Redis Cache Layer (Rate limiting, Context caching, Sessions)
✅ Reorganized LangGraph as "Execution Engine" with clear components
✅ Separated Database Connection Pool from PostgreSQL
✅ Added External Dependencies section
✅ Cleaner data flow from top to bottom
```

### Level 3: Component Diagram (Code-Level Design)

#### Core Components with OOP & Abstraction

```
┌─────────────────────────────────────────────────────────────────┐
│                    Component Architecture                        │
│                                                                  │
│  1. API Layer                                                    │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ Abstract Base Controller                            │     │
│     │  - handle_request()                                 │     │
│     │  - validate_input()                                 │     │
│     │  - format_response()                                │     │
│     └────────────┬────────────────────────────────────────┘     │
│                  │                                              │
│         ┌────────┴────────┬──────────────────┐                 │
│         ▼                 ▼                  ▼                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Chatbot    │  │ Conversation │  │    User      │         │
│  │  Controller  │  │  Controller  │  │  Controller  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  2. Service Layer                                               │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ Abstract Base Service                               │     │
│     │  - execute()                                        │     │
│     │  - validate()                                       │     │
│     │  - handle_error()                                   │     │
│     └────────────┬────────────────────────────────────────┘     │
│                  │                                              │
│         ┌────────┴────────┬──────────────────┐                 │
│         ▼                 ▼                  ▼                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Chatbot    │  │ Conversation │  │    User      │         │
│  │   Service    │  │   Service    │  │   Service    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  3. LangGraph Layer                                             │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ Abstract Graph Component                            │     │
│     │  - build_graph()                                    │     │
│     │  - execute_node()                                   │     │
│     │  - define_edges()                                   │     │
│     └────────────┬────────────────────────────────────────┘     │
│                  │                                              │
│         ┌────────┴────────┬──────────────────┐                 │
│         ▼                 ▼                  ▼                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  LLM Node    │  │ Context Node │  │ Response Node│         │
│  │   Handler    │  │   Handler    │  │   Handler    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  4. Repository Layer                                            │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ Abstract Base Repository                            │     │
│     │  - get_by_id()                                      │     │
│     │  - create()                                         │     │
│     │  - update()                                         │     │
│     │  - delete()                                         │     │
│     │  - find_all()                                       │     │
│     └────────────┬────────────────────────────────────────┘     │
│                  │                                              │
│         ┌────────┴────────┬──────────────────┐                 │
│         ▼                 ▼                  ▼                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Conversation │  │     User     │  │   Message    │         │
│  │  Repository  │  │  Repository  │  │  Repository  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  5. Domain Layer                                                │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ Abstract Base Entity                                │     │
│     │  - to_dict()                                        │     │
│     │  - from_dict()                                      │     │
│     │  - validate()                                       │     │
│     └────────────┬────────────────────────────────────────┘     │
│                  │                                              │
│         ┌────────┴────────┬──────────────────┐                 │
│         ▼                 ▼                  ▼                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Conversation │  │     User     │  │   Message    │         │
│  │    Entity    │  │    Entity    │  │    Entity    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
vpaura-be/
│
├── pyproject.toml                 # Project dependencies & config
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
├── README.md                      # Project documentation
│
├── alembic/                       # Database migrations
│   ├── versions/                  # Migration scripts
│   ├── env.py                     # Alembic environment
│   └── alembic.ini               # Alembic configuration
│
├── src/
│   ├── __init__.py
│   │
│   ├── main.py                    # FastAPI application entry point
│   │
│   ├── config/                    # Configuration
│   │   ├── __init__.py
│   │   ├── settings.py           # App settings (Pydantic)
│   │   └── database.py           # Database configuration
│   │
│   ├── api/                       # API Layer
│   │   ├── __init__.py
│   │   ├── dependencies.py       # FastAPI dependencies
│   │   ├── routes/               # API routes
│   │   │   ├── __init__.py
│   │   │   ├── chatbot.py       # Chatbot endpoints
│   │   │   ├── conversation.py  # Conversation endpoints
│   │   │   └── user.py          # User endpoints
│   │   └── controllers/          # Controllers (Abstract)
│   │       ├── __init__.py
│   │       ├── base.py          # Abstract base controller
│   │       ├── chatbot.py       # Chatbot controller
│   │       ├── conversation.py  # Conversation controller
│   │       └── user.py          # User controller
│   │
│   ├── services/                  # Service Layer
│   │   ├── __init__.py
│   │   ├── base.py               # Abstract base service
│   │   ├── chatbot.py           # Chatbot service
│   │   ├── conversation.py      # Conversation service
│   │   └── user.py              # User service
│   │
│   ├── langgraph/                 # LangGraph Integration
│   │   ├── __init__.py
│   │   ├── base.py               # Abstract graph component
│   │   ├── graph_builder.py     # Graph construction
│   │   ├── nodes/                # Graph nodes
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Abstract node
│   │   │   ├── llm_node.py      # LLM interaction node
│   │   │   ├── context_node.py  # Context retrieval node
│   │   │   └── response_node.py # Response formatting node
│   │   ├── edges/                # Graph edges
│   │   │   ├── __init__.py
│   │   │   └── conditions.py    # Edge conditions
│   │   └── state/                # Graph state
│   │       ├── __init__.py
│   │       └── chat_state.py    # Chat state management
│   │
│   ├── repositories/              # Repository Layer
│   │   ├── __init__.py
│   │   ├── base.py               # Abstract base repository
│   │   ├── conversation.py      # Conversation repository
│   │   ├── user.py              # User repository
│   │   └── message.py           # Message repository
│   │
│   ├── models/                    # Database Models (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── base.py               # Base model
│   │   ├── conversation.py      # Conversation model
│   │   ├── user.py              # User model
│   │   └── message.py           # Message model
│   │
│   ├── schemas/                   # Pydantic Schemas (DTOs)
│   │   ├── __init__.py
│   │   ├── base.py               # Base schema
│   │   ├── chatbot.py           # Chatbot schemas
│   │   ├── conversation.py      # Conversation schemas
│   │   ├── user.py              # User schemas
│   │   └── message.py           # Message schemas
│   │
│   ├── core/                      # Core utilities
│   │   ├── __init__.py
│   │   ├── logger.py            # Logging configuration
│   │   └── streaming.py         # Streaming utilities
│   │
│   ├── constants/                 # Constants & Enums
│   │   ├── __init__.py
│   │   ├── messages.py          # Message constants
│   │   ├── errors.py            # Error message constants
│   │   ├── enums.py             # Common enums
│   │   └── config.py            # Configuration constants
│   │
│   ├── database/                  # Database Connection
│   │   ├── __init__.py
│   │   ├── session.py           # Async session factory
│   │   ├── connection.py        # Database connection pool
│   │   └── engine.py            # SQLAlchemy async engine
│   │
│   ├── exceptions/                # Custom Exceptions
│   │   ├── __init__.py
│   │   ├── base.py              # Base exception classes
│   │   ├── api.py               # API-related exceptions
│   │   ├── database.py          # Database exceptions
│   │   └── service.py           # Service layer exceptions
│   │
│   ├── middleware/                # Middleware Components
│   │   ├── __init__.py
│   │   ├── dependencies.py      # FastAPI dependencies
│   │   ├── metrics.py           # Metrics collection
│   │   ├── middleware.py        # Custom middleware
│   │   └── rate_limiter.py      # Rate limiting
│   │
│   └── utils/                     # Helper utilities
│       ├── __init__.py
│       ├── helpers.py            # Common helpers
│       ├── validators.py         # Input validators
│       ├── formatters.py         # Data formatters
│       └── converters.py         # Type converters
│
└── tests/                         # Tests
    ├── __init__.py
    ├── conftest.py               # Pytest configuration
    ├── unit/                     # Unit tests
    └── integration/              # Integration tests
```

---

## 🏗️ Implementation Plan

### Phase 1: Project Setup & Foundation

#### Step 1.1: Initialize Project Structure
```bash
# Create project structure
mkdir -p src/{api/{routes,controllers},services,langgraph/{nodes,edges,state},repositories,models,schemas,core,constants,database,exceptions,middleware,utils,config}
mkdir -p alembic/versions
mkdir -p tests/{unit,integration}

# Create __init__.py files
find src -type d -exec touch {}/__init__.py \;
find tests -type d -exec touch {}/__init__.py \;
```

#### Step 1.2: Setup pyproject.toml
```toml
[tool.poetry]
name = "vpaura"
version = "0.1.0"
description = "AI Chatbot with streaming capabilities"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
sqlalchemy = "^2.0.0"
alembic = "^1.12.0"
pydantic = "^2.4.0"
pydantic-settings = "^2.0.0"
langgraph = "^0.0.40"
langchain = "^0.1.0"
langchain-openai = "^0.0.2"
python-dotenv = "^1.0.0"
asyncpg = "^0.29.0"
psycopg2-binary = "^2.9.9"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
black = "^23.10.0"
ruff = "^0.1.0"
mypy = "^1.6.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

#### Step 1.3: Environment Configuration
```python
# src/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "VPAura"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    
    # LLM
    OPENAI_API_KEY: str
    LLM_MODEL: str = "gpt-4"
    
    # API
    API_PREFIX: str = "/api/v1"
    
    class Config:
        env_file = ".env"
```

#### Step 1.4: Constants & Enums Setup
```python
# src/constants/enums.py
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ConversationStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
```

```python
# src/constants/messages.py
class Messages:
    # Success messages
    USER_CREATED = "User created successfully"
    CONVERSATION_CREATED = "Conversation created successfully"
    MESSAGE_SENT = "Message sent successfully"
    
    # Error messages
    USER_NOT_FOUND = "User not found"
    CONVERSATION_NOT_FOUND = "Conversation not found"
    INVALID_INPUT = "Invalid input provided"
    DATABASE_ERROR = "Database operation failed"
    LLM_ERROR = "LLM service unavailable"
    
    # Validation messages
    REQUIRED_FIELD = "This field is required"
    INVALID_EMAIL = "Invalid email format"
    INVALID_MESSAGE = "Message cannot be empty"
```

```python
# src/constants/errors.py
class ErrorMessages:
    # API Errors
    INVALID_REQUEST = "Invalid request format"
    MISSING_PARAMETERS = "Missing required parameters"
    
    # Database Errors
    CONNECTION_FAILED = "Database connection failed"
    TRANSACTION_FAILED = "Transaction failed"
    
    # Service Errors
    SERVICE_UNAVAILABLE = "Service temporarily unavailable"
    RATE_LIMIT_EXCEEDED = "Rate limit exceeded"
```

```python
# src/constants/config.py
class Config:
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW = 60  # seconds
    
    # Streaming
    STREAM_CHUNK_SIZE = 1024
    STREAM_TIMEOUT = 30
```

#### Step 1.5: Database Connection Setup
```python
# src/database/engine.py
from sqlalchemy.ext.asyncio import create_async_engine
from ..config.settings import Settings

settings = Settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

```python
# src/database/session.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from .engine import engine

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_async_session() -> AsyncSession:
    """Dependency for getting async database session"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

```python
# src/database/connection.py
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncConnection
from .engine import engine

@asynccontextmanager
async def get_connection():
    """Get database connection from pool"""
    async with engine.begin() as conn:
        yield conn

async def check_connection() -> bool:
    """Check if database connection is alive"""
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception:
        return False
```

#### Step 1.6: Exception Hierarchy Setup
```python
# src/exceptions/base.py
from typing import Optional, Dict, Any

class VPAuraException(Exception):
    """Base exception for VPAura application"""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationException(VPAuraException):
    """Validation error exception"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )

class NotFoundException(VPAuraException):
    """Resource not found exception"""
    
    def __init__(self, message: str, resource: str):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource}
        )
```

```python
# src/exceptions/api.py
from .base import VPAuraException

class APIException(VPAuraException):
    """Base API exception"""
    pass

class UnauthorizedException(APIException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401
        )

class ForbiddenException(APIException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403
        )

class RateLimitException(APIException):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429
        )
```

```python
# src/exceptions/database.py
from .base import VPAuraException

class DatabaseException(VPAuraException):
    """Base database exception"""
    pass

class ConnectionException(DatabaseException):
    def __init__(self, message: str = "Database connection failed"):
        super().__init__(
            message=message,
            code="DB_CONNECTION_ERROR",
            status_code=503
        )

class TransactionException(DatabaseException):
    def __init__(self, message: str = "Transaction failed"):
        super().__init__(
            message=message,
            code="DB_TRANSACTION_ERROR",
            status_code=500
        )
```

```python
# src/exceptions/service.py
from .base import VPAuraException

class ServiceException(VPAuraException):
    """Base service exception"""
    pass

class LLMException(ServiceException):
    def __init__(self, message: str = "LLM service error"):
        super().__init__(
            message=message,
            code="LLM_ERROR",
            status_code=503
        )

class GraphException(ServiceException):
    def __init__(self, message: str = "Graph execution failed"):
        super().__init__(
            message=message,
            code="GRAPH_ERROR",
            status_code=500
        )
```

#### Step 1.7: Middleware Setup
```python
# src/middleware/middleware.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
import logging

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses"""
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} "
            f"(took {process_time:.2f}s)"
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        return response

class CORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware"""
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response
```

```python
# src/middleware/dependencies.py
from fastapi import Depends, Header, HTTPException
from typing import Optional
from ..database.session import get_async_session
from ..constants.errors import ErrorMessages
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db_session() -> AsyncSession:
    """Database session dependency"""
    async for session in get_async_session():
        yield session

async def verify_api_key(
    x_api_key: Optional[str] = Header(None)
) -> str:
    """Verify API key from header"""
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail=ErrorMessages.INVALID_REQUEST
        )
    # Add your API key validation logic here
    return x_api_key

async def get_current_user(
    api_key: str = Depends(verify_api_key),
    session: AsyncSession = Depends(get_db_session)
):
    """Get current user from API key"""
    # Implement user retrieval logic
    pass
```

```python
# src/middleware/metrics.py
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Request
import time

# Metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

llm_request_count = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['model', 'status']
)

llm_token_count = Counter(
    'llm_tokens_total',
    'Total LLM tokens used',
    ['model', 'type']
)

class MetricsMiddleware:
    """Middleware for collecting metrics"""
    
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        # Record metrics
        duration = time.time() - start_time
        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response

def get_metrics():
    """Get Prometheus metrics"""
    return generate_latest()
```

```python
# src/middleware/rate_limiter.py
from fastapi import Request, HTTPException
from typing import Dict, Tuple
import time
from collections import defaultdict
from ..constants.config import Config
from ..constants.errors import ErrorMessages

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(
        self,
        requests: int = Config.RATE_LIMIT_REQUESTS,
        window: int = Config.RATE_LIMIT_WINDOW
    ):
        self.requests = requests
        self.window = window
        self.clients: Dict[str, Tuple[int, float]] = defaultdict(
            lambda: (requests, time.time())
        )
    
    async def __call__(self, request: Request):
        """Check rate limit for client"""
        client_id = self._get_client_id(request)
        
        tokens, last_update = self.clients[client_id]
        now = time.time()
        
        # Refill tokens based on time passed
        time_passed = now - last_update
        tokens = min(
            self.requests,
            tokens + (time_passed * self.requests / self.window)
        )
        
        if tokens < 1:
            raise HTTPException(
                status_code=429,
                detail=ErrorMessages.RATE_LIMIT_EXCEEDED
            )
        
        # Consume one token
        self.clients[client_id] = (tokens - 1, now)
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Try to get from API key, fallback to IP
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"key:{api_key}"
        
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0]}"
        
        return f"ip:{request.client.host}"
```

#### Step 1.8: Enhanced Utils
```python
# src/utils/validators.py
import re
from typing import Any, Optional
from ..constants.messages import Messages
from ..exceptions.base import ValidationException

class Validator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationException(Messages.INVALID_EMAIL)
        return True
    
    @staticmethod
    def validate_not_empty(value: str, field_name: str) -> bool:
        """Validate string is not empty"""
        if not value or not value.strip():
            raise ValidationException(
                f"{field_name}: {Messages.REQUIRED_FIELD}"
            )
        return True
    
    @staticmethod
    def validate_range(
        value: int,
        min_val: Optional[int] = None,
        max_val: Optional[int] = None
    ) -> bool:
        """Validate numeric range"""
        if min_val is not None and value < min_val:
            raise ValidationException(f"Value must be >= {min_val}")
        if max_val is not None and value > max_val:
            raise ValidationException(f"Value must be <= {max_val}")
        return True
```

```python
# src/utils/formatters.py
from datetime import datetime
from typing import Any, Dict

class Formatter:
    """Data formatting utilities"""
    
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """Format datetime to ISO string"""
        return dt.isoformat()
    
    @staticmethod
    def format_response(
        data: Any,
        message: str = "Success",
        status: str = "success"
    ) -> Dict[str, Any]:
        """Format API response"""
        return {
            "status": status,
            "message": message,
            "data": data
        }
    
    @staticmethod
    def format_error(
        message: str,
        code: str = "ERROR",
        details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Format error response"""
        return {
            "status": "error",
            "code": code,
            "message": message,
            "details": details or {}
        }
```

```python
# src/utils/converters.py
from typing import Dict, Any, List
from datetime import datetime

class Converter:
    """Type conversion utilities"""
    
    @staticmethod
    def dict_to_snake_case(data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert dict keys to snake_case"""
        result = {}
        for key, value in data.items():
            snake_key = ''.join(
                ['_' + c.lower() if c.isupper() else c for c in key]
            ).lstrip('_')
            result[snake_key] = value
        return result
    
    @staticmethod
    def model_to_dict(model: Any) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dict"""
        result = {}
        for column in model.__table__.columns:
            value = getattr(model, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
```

### Phase 2: Database Layer (Bottom-Up Approach)

#### Step 2.1: Base Model & Abstract Repository
```python
# src/models/base.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
```

```python
# src/repositories/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[T]:
        pass
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def delete(self, id: int) -> bool:
        pass
    
    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        pass
```

#### Step 2.2: Domain Models
```python
# src/models/user.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class User(Base):
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100))
    conversations: Mapped[List["Conversation"]] = relationship(
        back_populates="user"
    )
```

```python
# src/models/conversation.py
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class Conversation(Base):
    __tablename__ = "conversations"
    
    title: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(
        back_populates="conversation"
    )
```

```python
# src/models/message.py
from sqlalchemy import ForeignKey, String, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from ..constants.enums import MessageRole

class Message(Base):
    __tablename__ = "messages"
    
    content: Mapped[str] = mapped_column(Text)
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole))
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    
    conversation: Mapped["Conversation"] = relationship(
        back_populates="messages"
    )
```

#### Step 2.3: Alembic Setup
```bash
# Initialize Alembic
alembic init alembic

# Configure alembic.ini and env.py
# Create initial migration
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### Phase 3: LangGraph Integration Layer

#### Step 3.1: Abstract Graph Components
```python
# src/langgraph/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict
from langgraph.graph import StateGraph

class BaseGraphComponent(ABC):
    @abstractmethod
    def build_graph(self) -> StateGraph:
        """Build and return the graph structure"""
        pass
    
    @abstractmethod
    async def execute_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single node"""
        pass
```

```python
# src/langgraph/state/chat_state.py
from typing import TypedDict, List, Optional

class ChatState(TypedDict):
    messages: List[Dict[str, str]]
    conversation_id: Optional[int]
    user_id: int
    context: Optional[str]
    current_response: Optional[str]
```

#### Step 3.2: Graph Nodes (Abstract → Concrete)
```python
# src/langgraph/nodes/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseNode(ABC):
    @abstractmethod
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute node logic"""
        pass
    
    @abstractmethod
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """Validate node input"""
        pass
```

```python
# src/langgraph/nodes/llm_node.py
from .base import BaseNode
from langchain_openai import ChatOpenAI

class LLMNode(BaseNode):
    def __init__(self, model_name: str):
        self.llm = ChatOpenAI(model=model_name)
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # LLM interaction logic
        response = await self.llm.ainvoke(state["messages"])
        state["current_response"] = response.content
        return state
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        return "messages" in state and len(state["messages"]) > 0
```

#### Step 3.3: Graph Builder
```python
# src/langgraph/graph_builder.py
from langgraph.graph import StateGraph, END
from .nodes import LLMNode, ContextNode, ResponseNode
from .state import ChatState

class ChatGraphBuilder:
    def __init__(self):
        self.graph = StateGraph(ChatState)
    
    def build(self) -> StateGraph:
        # Add nodes
        self.graph.add_node("retrieve_context", ContextNode())
        self.graph.add_node("llm_processing", LLMNode())
        self.graph.add_node("format_response", ResponseNode())
        
        # Define edges
        self.graph.add_edge("retrieve_context", "llm_processing")
        self.graph.add_edge("llm_processing", "format_response")
        self.graph.add_edge("format_response", END)
        
        # Set entry point
        self.graph.set_entry_point("retrieve_context")
        
        return self.graph.compile()
```

### Phase 4: Service Layer (Business Logic)

#### Step 4.1: Abstract Service
```python
# src/services/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar('T')
R = TypeVar('R')

class BaseService(ABC, Generic[T, R]):
    @abstractmethod
    async def execute(self, input_data: T) -> R:
        """Execute service logic"""
        pass
    
    @abstractmethod
    def validate(self, input_data: T) -> bool:
        """Validate input"""
        pass
    
    @abstractmethod
    async def handle_error(self, error: Exception) -> None:
        """Handle errors"""
        pass
```

#### Step 4.2: Chatbot Service
```python
# src/services/chatbot.py
from .base import BaseService
from ..langgraph.graph_builder import ChatGraphBuilder
from ..schemas.chatbot import ChatRequest, ChatResponse
from typing import AsyncGenerator

class ChatbotService(BaseService[ChatRequest, AsyncGenerator[str, None]]):
    def __init__(self):
        self.graph = ChatGraphBuilder().build()
    
    async def execute(self, input_data: ChatRequest) -> AsyncGenerator[str, None]:
        """Stream chatbot response"""
        state = {
            "messages": input_data.messages,
            "user_id": input_data.user_id,
            "conversation_id": input_data.conversation_id
        }
        
        async for chunk in self.graph.astream(state):
            if "current_response" in chunk:
                yield chunk["current_response"]
    
    def validate(self, input_data: ChatRequest) -> bool:
        return len(input_data.messages) > 0
    
    async def handle_error(self, error: Exception) -> None:
        # Error logging and handling
        pass
```

### Phase 5: API Layer

#### Step 5.1: Abstract Controller
```python
# src/api/controllers/base.py
from abc import ABC, abstractmethod
from typing import Any
from fastapi import Request

class BaseController(ABC):
    @abstractmethod
    async def handle_request(self, request: Request) -> Any:
        """Handle incoming request"""
        pass
    
    @abstractmethod
    def validate_input(self, data: Any) -> bool:
        """Validate request data"""
        pass
    
    @abstractmethod
    def format_response(self, data: Any) -> Any:
        """Format response"""
        pass
```

#### Step 5.2: Chatbot Controller & Routes
```python
# src/api/controllers/chatbot.py
from .base import BaseController
from ...services.chatbot import ChatbotService
from ...schemas.chatbot import ChatRequest

class ChatbotController(BaseController):
    def __init__(self):
        self.service = ChatbotService()
    
    async def handle_request(self, request: ChatRequest):
        return await self.service.execute(request)
```

```python
# src/api/routes/chatbot.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from ..controllers.chatbot import ChatbotController
from ...schemas.chatbot import ChatRequest
from ...middleware.dependencies import get_db_session, get_current_user
from ...middleware.rate_limiter import RateLimiter

router = APIRouter(prefix="/chat", tags=["chatbot"])
rate_limiter = RateLimiter()

@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    controller: ChatbotController = Depends(),
    _rate_limit = Depends(rate_limiter),
    _current_user = Depends(get_current_user)
):
    """Stream chatbot responses"""
    return StreamingResponse(
        controller.handle_request(request),
        media_type="text/event-stream"
    )
```

#### Step 5.3: Main Application
```python
# src/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .api.routes import chatbot, conversation, user
from .config.settings import Settings
from .middleware.middleware import LoggingMiddleware, CORSMiddleware
from .middleware.metrics import MetricsMiddleware, get_metrics
from .exceptions.base import VPAuraException
from .database.connection import check_connection
from .constants.messages import Messages

settings = Settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="VPAura AI Chatbot API with streaming capabilities"
)

# Add middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(CORSMiddleware)
app.add_middleware(MetricsMiddleware)

# Exception handlers
@app.exception_handler(VPAuraException)
async def vpaura_exception_handler(request: Request, exc: VPAuraException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )

# Include routers
app.include_router(chatbot.router, prefix="/api/v1")
app.include_router(conversation.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = await check_connection()
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "version": settings.APP_VERSION
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return get_metrics()

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    # Check database connection
    if not await check_connection():
        raise Exception(Messages.DATABASE_ERROR)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    from .database.engine import engine
    await engine.dispose()
```

### Phase 6: Streaming Implementation

#### Step 6.1: Streaming Utilities
```python
# src/core/streaming.py
from typing import AsyncGenerator
import asyncio

class StreamingResponse:
    @staticmethod
    async def stream_generator(
        content: AsyncGenerator[str, None]
    ) -> AsyncGenerator[str, None]:
        """Format streaming response for SSE"""
        async for chunk in content:
            yield f"data: {chunk}\n\n"
            await asyncio.sleep(0)  # Allow other tasks to run
        
        yield "data: [DONE]\n\n"
```

### Phase 7: Testing & Documentation

#### Step 7.1: Unit Tests
```python
# tests/unit/test_chatbot_service.py
import pytest
from src.services.chatbot import ChatbotService
from src.schemas.chatbot import ChatRequest

@pytest.mark.asyncio
async def test_chatbot_service():
    service = ChatbotService()
    request = ChatRequest(
        messages=[{"role": "user", "content": "Hello"}],
        user_id=1
    )
    
    response = []
    async for chunk in service.execute(request):
        response.append(chunk)
    
    assert len(response) > 0
```

#### Step 7.2: Integration Tests
```python
# tests/integration/test_chatbot_api.py
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_stream_chat_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat/stream",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "user_id": 1
            }
        )
        assert response.status_code == 200
```

---

## 🎯 Key Design Principles

### 1. **Abstraction First**
- Every layer has an abstract base class
- Concrete implementations extend abstractions
- Easy to swap implementations (e.g., different LLM providers)

### 2. **Separation of Concerns**
- **API Layer**: Handle HTTP requests/responses
- **Service Layer**: Business logic
- **Repository Layer**: Data access
- **Domain Layer**: Business entities

### 3. **Dependency Injection**
- FastAPI's `Depends()` for DI
- Easy testing and mocking
- Loose coupling between components

### 4. **Streaming Architecture**
- Async/await throughout
- Generator patterns for streaming
- SSE (Server-Sent Events) for real-time updates

### 5. **Type Safety**
- Pydantic for validation
- Type hints everywhere
- Static type checking with mypy

---

## 🚀 Deployment Considerations

### Docker Configuration
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN poetry install --no-dev

# Copy application
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

# Run migrations and start app
CMD poetry run alembic upgrade head && \
    poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Environment Variables (.env)
```env
# Application
APP_NAME=VPAura
APP_VERSION=0.1.0
DEBUG=false

# Database (PostgreSQL via Docker)
DATABASE_URL=postgresql+asyncpg://vpaura:vpaura123@localhost:5432/vpaura_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# LLM Configuration
OPENAI_API_KEY=sk-xxx
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# API Configuration
API_PREFIX=/api/v1
ALLOWED_ORIGINS=*

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
```

### Docker Compose for PostgreSQL
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: vpaura-postgres
    environment:
      POSTGRES_USER: vpaura
      POSTGRES_PASSWORD: vpaura123
      POSTGRES_DB: vpaura_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U vpaura"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: vpaura-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## 📊 API Endpoints

### Chat Endpoints
- `POST /api/v1/chat/stream` - Stream chat responses
- `POST /api/v1/chat/message` - Send single message

### Conversation Endpoints
- `GET /api/v1/conversations` - List conversations
- `POST /api/v1/conversations` - Create conversation
- `GET /api/v1/conversations/{id}` - Get conversation
- `DELETE /api/v1/conversations/{id}` - Delete conversation

### User Endpoints
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/{id}` - Get user
- `PUT /api/v1/users/{id}` - Update user

---

## 🔄 Development Workflow

1. **Setup**: Initialize project, install dependencies
2. **Docker**: Start PostgreSQL container (`docker-compose up -d`)
3. **Constants**: Define all enums and message constants
4. **Database**: Create models, migrations, connection pool
5. **Exceptions**: Set up exception hierarchy
6. **Middleware**: Configure rate limiting, logging, metrics
7. **LangGraph**: Build conversation graph
8. **Services**: Implement business logic
9. **API**: Create endpoints
10. **Testing**: Write tests
11. **Documentation**: API docs (auto-generated by FastAPI)
12. **Deployment**: Docker, CI/CD

### Quick Start Commands

```bash
# 1. Start PostgreSQL
docker-compose up -d postgres

# 2. Install dependencies
poetry install

# 3. Run database migrations
poetry run alembic upgrade head

# 4. Start development server
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 5. Access API docs
# http://localhost:8000/docs
```

---

## 📝 Next Steps

1. ✅ Review this plan
2. � Setup Docker PostgreSQL database
3. 📋 Define all constants and enums (no hardcoded strings!)
4. 🗄️ Setup database connection pool and async session
5. ⚠️ Create exception hierarchy
6. 🔧 Implement middleware (rate limiting, logging, metrics)
7. �🔨 Start with Phase 1: Project setup
8. 🗄️ Implement database layer (Phase 2)
9. 🤖 Integrate LangGraph (Phase 3)
10. 💼 Build services (Phase 4)
11. 🌐 Create APIs (Phase 5)
12. 📡 Implement streaming (Phase 6)
13. 🧪 Write tests (Phase 7)
14. 🚀 Deploy to production

## 🎯 Key Architectural Improvements

### 1. **Constants-First Approach**
- ❌ NO hardcoded strings: `"user not found"`
- ✅ USE constants: `Messages.USER_NOT_FOUND`
- ✅ PREFER enums: `MessageRole.USER` instead of `"user"`

### 2. **Database Connection Best Practices**
- Async connection pool with SQLAlchemy 2.0
- Health checks and connection validation
- Proper session management with context managers
- Docker-based PostgreSQL for development

### 3. **Exception Handling**
- Hierarchical exception structure
- Consistent error responses
- HTTP status code mapping
- Detailed error context

### 4. **Middleware Stack**
- Request/response logging
- Metrics collection (Prometheus)
- Rate limiting (token bucket)
- CORS handling
- Custom dependencies for auth

### 5. **Utilities Organization**
- Validators: Input validation logic
- Formatters: Response formatting
- Converters: Type conversions
- Helpers: General utilities

---

**Note**: This plan follows a bottom-up approach with strong OOP principles, making the system highly extensible and maintainable. Each layer is abstracted, allowing for easy modifications and additions in the future.
