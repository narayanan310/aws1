"""Domain-specific exceptions."""


class AppError(Exception):
    """Base application exception."""


class AuthorizationError(AppError):
    """Raised when ownership or permission checks fail."""


class ValidationError(AppError):
    """Raised when user input is invalid."""


class NotFoundError(AppError):
    """Raised when an entity cannot be found."""

