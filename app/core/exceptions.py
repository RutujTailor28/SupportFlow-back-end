"""Application-specific exceptions and error responses."""

from typing import Any


class AppError(Exception):
    """Base application error with HTTP status and machine-readable code."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "APP_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppError):
    """Resource was not found."""

    def __init__(self, message: str = "Resource not found", *, code: str = "NOT_FOUND") -> None:
        super().__init__(message, code=code, status_code=404)


class TicketNotFoundError(NotFoundError):
    """Ticket was not found."""

    def __init__(self, ticket_id: str) -> None:
        super().__init__(message="Ticket not found", code="TICKET_NOT_FOUND")
        self.ticket_id = ticket_id


class DatabaseError(AppError):
    """Database operation failed."""

    def __init__(self, message: str = "Database operation failed") -> None:
        super().__init__(message, code="DATABASE_ERROR", status_code=500)
