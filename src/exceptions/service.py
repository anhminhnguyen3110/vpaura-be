from .base import VPAuraException


class ServiceException(VPAuraException):
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
