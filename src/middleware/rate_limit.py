"""Rate limiting configuration for the application.

This module configures rate limiting using slowapi, with default limits
defined in the application settings. Rate limits are applied based on
remote IP addresses.

Note: This is currently not in use. To enable, install slowapi:
    pip install slowapi
    
Then configure in settings and apply to routes.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from ..config.settings import settings


# Create limiter instance with IP-based rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=getattr(settings, 'RATE_LIMIT_DEFAULT', ["100/minute"])
)


# Example usage (not currently active):
# 
# In main.py:
#     from slowapi import _rate_limit_exceeded_handler
#     from slowapi.errors import RateLimitExceeded
#     
#     app.state.limiter = limiter
#     app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
#
# In routes:
#     @router.get("/endpoint")
#     @limiter.limit("10/minute")
#     async def my_endpoint(request: Request):
#         ...
