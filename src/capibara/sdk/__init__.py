"""SDK for Capibara Core."""

from .client import CapibaraClient
from .exceptions import CapibaraError, ScriptGenerationError, ExecutionError, SecurityError

__all__ = [
    "CapibaraClient",
    "CapibaraError",
    "ScriptGenerationError", 
    "ExecutionError",
    "SecurityError",
]
