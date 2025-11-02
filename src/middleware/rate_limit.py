"""Rate limiting configuration using slowapi (currently disabled).

Note: To enable, install slowapi and configure in main.py and routes.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from ..config.settings import settings


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=getattr(settings, 'RATE_LIMIT_DEFAULT', ["100/minute"])
)
