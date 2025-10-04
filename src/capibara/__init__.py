"""
Capibara Core - A secure, production-ready developer tool for generating executable scripts.

This package provides a modular architecture for generating and executing scripts
from natural language prompts using multiple LLM providers with comprehensive
security controls and sandboxed execution.
"""

__version__ = "0.1.0"
__author__ = "Capibara Team"

from capibara.sdk.client import CapibaraClient
from capibara.models.requests import RunRequest, ListRequest
from capibara.models.responses import RunResponse, ListResponse, ScriptInfo

__all__ = [
    "CapibaraClient",
    "RunRequest",
    "ListRequest", 
    "RunResponse",
    "ListResponse",
    "ScriptInfo",
]
