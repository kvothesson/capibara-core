"""Exceptions for Capibara SDK."""


class CapibaraError(Exception):
    """Base exception for Capibara SDK."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ScriptGenerationError(CapibaraError):
    """Raised when script generation fails."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details)


class ExecutionError(CapibaraError):
    """Raised when script execution fails."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details)


class SecurityError(CapibaraError):
    """Raised when security checks fail."""

    def __init__(self, message: str, violations: list = None, details: dict = None):
        super().__init__(message, details)
        self.violations = violations or []


class CacheError(CapibaraError):
    """Raised when cache operations fail."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details)


class LLMProviderError(CapibaraError):
    """Raised when LLM provider operations fail."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details)


class ContainerError(CapibaraError):
    """Raised when container operations fail."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details)


class PolicyError(CapibaraError):
    """Raised when security policy operations fail."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details)


class ValidationError(CapibaraError):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details)
