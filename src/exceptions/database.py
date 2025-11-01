from .base import VPAuraException


class DatabaseException(VPAuraException):
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
