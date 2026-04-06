"""Application-level exceptions and error codes."""

from __future__ import annotations


class AppError(Exception):
    """Base application error."""

    def __init__(self, code: int, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, resource: str, resource_id: str | int) -> None:
        super().__init__(
            code=404,
            message=f"{resource} not found: {resource_id}",
            status_code=404,
        )


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(code=409, message=message, status_code=409)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(code=403, message=message, status_code=403)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(code=401, message=message, status_code=401)


class ValidationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(code=422, message=message, status_code=422)


class ExternalServiceError(AppError):
    def __init__(self, service: str, message: str) -> None:
        super().__init__(
            code=502,
            message=f"External service error [{service}]: {message}",
            status_code=502,
        )
