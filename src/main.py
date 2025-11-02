from contextlib import asynccontextmanager
from typing import Dict, Any
from datetime import datetime
import os

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from .api.routes import chatbot, user, conversation, message, document
from .config.settings import settings
from .constants.config import Config
from .middleware.middleware import LoggingMiddleware
from .middleware.metrics import MetricsMiddleware, get_metrics
from .exceptions.handlers import setup_exception_handlers
from .exceptions.database import DatabaseException
from .database.connection import check_connection
from .constants.messages import Messages
from .core.logger import logger

# Set Langfuse environment variables if enabled
if settings.LANGFUSE_ENABLED:
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
    os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
    os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST
    logger.info("Langfuse environment variables configured")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    logger.info(
        "application_startup",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT.value,
    )
    
    if not await check_connection():
        logger.error("database_connection_failed")
        raise DatabaseException(Messages.DATABASE_ERROR)
    
    yield
    
    logger.info("application_shutdown")
    try:
        from .database.engine import engine
        await engine.dispose()
    except Exception as e:
        logger.warning("engine_disposal_failed", error=str(e))


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="VPAura AI Chatbot API with streaming capabilities",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(MetricsMiddleware)

setup_exception_handlers(app)

app.include_router(chatbot.router, prefix=Config.API_V1_PREFIX)
app.include_router(user.router, prefix=Config.API_V1_PREFIX)
app.include_router(conversation.router, prefix=Config.API_V1_PREFIX)
app.include_router(message.router, prefix=Config.API_V1_PREFIX)
app.include_router(document.router, prefix=Config.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to VPAura AI Chatbot API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_status = await check_connection()
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from starlette.responses import Response
    return Response(content=get_metrics(), media_type="text/plain")


@app.get("/info")
async def info(request: Request) -> Dict[str, Any]:
    """Information endpoint with system details."""
    logger.info("info_endpoint_called")
    
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT.value,
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )
