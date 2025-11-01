from .base import VPAuraException


class APIException(VPAuraException):
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
