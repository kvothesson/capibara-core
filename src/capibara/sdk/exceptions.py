"""Exceptions for Capibara SDK."""


class CapibaraError(Exception):
    """Base exception for Capibara SDK."""
    pass


class ScriptGenerationError(CapibaraError):
    """Raised when script generation fails."""
    pass


class ExecutionError(CapibaraError):
    """Raised when script execution fails."""
    pass


class SecurityError(CapibaraError):
    """Raised when security checks fail."""
    
    def __init__(self, message: str, violations: list = None):
        super().__init__(message)
        self.violations = violations or []


class CacheError(CapibaraError):
    """Raised when cache operations fail."""
    pass


class LLMProviderError(CapibaraError):
    """Raised when LLM provider operations fail."""
    pass


class ContainerError(CapibaraError):
    """Raised when container operations fail."""
    pass


class PolicyError(CapibaraError):
    """Raised when security policy operations fail."""
    pass


class ValidationError(CapibaraError):
    """Raised when input validation fails."""
    pass
