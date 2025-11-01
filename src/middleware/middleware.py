from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
import logging

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        start_time = time.time()
        
        logger.info(f"Request: {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} "
            f"(took {process_time:.2f}s)"
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        return response


class CORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response
