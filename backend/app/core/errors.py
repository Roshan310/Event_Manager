from typing import Any


class DomainError(Exception):
    def __init__(
        self, code: str, message: str, status_code: int = 400, details: Any = None
    ) -> None:
        self.code, self.message, self.status_code, self.details = (
            code,
            message,
            status_code,
            details,
        )
        super().__init__(message)


class NotFoundError(DomainError):
    def __init__(self, resource: str) -> None:
        super().__init__(
            f"{resource}_not_found", f"{resource.replace('_', ' ').title()} not found", 404
        )


class ForbiddenError(DomainError):
    def __init__(self, message: str = "You do not have permission to perform this action") -> None:
        super().__init__("forbidden", message, 403)


class ConflictError(DomainError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, 409)
