"""Domain exceptions for Plug."""


class PlugError(Exception):
    """Base exception for expected Plug failures."""


class PlanValidationError(PlugError, ValueError):
    """Raised when a task plan is invalid."""


class ProviderError(PlugError):
    """Raised when a provider operation fails."""


class UnknownProviderError(ProviderError, LookupError):
    """Raised when a provider name is not registered."""
