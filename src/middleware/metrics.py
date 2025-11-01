"""Prometheus metrics configuration and middleware.

This module provides comprehensive metrics tracking including:
- HTTP request metrics (count, duration)
- Database metrics (connections, query duration)
- LLM metrics (requests, tokens)
- Agent metrics (invocations, response time)
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, FastAPI
from starlette.responses import PlainTextResponse
from ..config.settings import settings
import time


# HTTP Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Database Metrics
db_connections = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type']
)

# LLM Metrics
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

llm_inference_duration_seconds = Histogram(
    'llm_inference_duration_seconds',
    'Time spent processing LLM inference',
    ['model'],
    buckets=[0.1, 0.3, 0.5, 1.0, 2.0, 5.0]
)

llm_stream_duration_seconds = Histogram(
    'llm_stream_duration_seconds',
    'Time spent processing LLM stream inference',
    ['model'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Agent Metrics
agent_invocations_total = Counter(
    'agent_invocations_total',
    'Total number of agent invocations',
    ['agent_type', 'status']
)

agent_response_time_seconds = Histogram(
    'agent_response_time_seconds',
    'Agent response time in seconds',
    ['agent_type']
)


class MetricsMiddleware:
    """Middleware for tracking HTTP request metrics."""

    def __init__(self, app):
        """Initialize the middleware.
        
        Args:
            app: The ASGI application
        """
        self.app = app

    async def __call__(self, scope, receive, send):
        """Track metrics for each request.

        Args:
            scope: The ASGI scope
            receive: The receive callable
            send: The send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        status_code = 500  # Default to 500 in case of exception

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.time() - start_time
            
            http_requests_total.labels(
                method=scope["method"],
                endpoint=scope["path"],
                status=status_code
            ).inc()

            http_request_duration_seconds.labels(
                method=scope["method"],
                endpoint=scope["path"]
            ).observe(duration)


def get_metrics():
    """Get current Prometheus metrics.
    
    Returns:
        bytes: Prometheus metrics in text format
    """
    return generate_latest()
