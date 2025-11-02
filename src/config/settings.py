from pydantic_settings import BaseSettings
from enum import Enum
from pathlib import Path


class Environment(str, Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    APP_NAME: str = "VPAura"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Environment
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    OPENAI_API_BASE: str = "https://openrouter.ai/api/v1"
    OPENAI_API_KEY: str
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "openai/gpt-4o-mini-2024-07-18"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000
    
    API_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: str = "*"
    
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
    
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "console"
    LOG_DIR: Path = Path("logs")
    
    REDIS_URL: str = "redis://localhost:6379"
    
    ENABLE_GUARDRAIL: bool = True
    
    # Neo4j Configuration
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4j"
    NEO4J_DATABASE: str = "neo4j"
    
    # Neo4j Agent Configuration
    NEO4J_AGENT_MAX_RETRIES: int = 3
    
    LANGFUSE_ENABLED: bool = False
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    
    class Config:
        env_file = ".env"


settings = Settings()
