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
    
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_API_KEY: str
    LLM_PROVIDER: str = "openai"  # openai, bedrock
    LLM_MODEL: str = "gpt-4"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000
    
    API_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: str = "*"
    
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
    
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "console"  # console, json
    LOG_DIR: Path = Path("logs")
    
    REDIS_URL: str = "redis://localhost:6379"
    
    ENABLE_GUARDRAIL: bool = True
    
    # LangFuse Configuration (disabled by default)
    LANGFUSE_ENABLED: bool = False
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    
    class Config:
        env_file = ".env"


settings = Settings()
