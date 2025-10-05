"""
Capibara Core - A secure, production-ready developer tool for generating executable scripts.

This package provides a modular architecture for generating and executing scripts
from natural language prompts using multiple LLM providers with comprehensive
security controls and sandboxed execution.
"""

__version__ = "0.1.0"
__author__ = "Capibara Team"

from capibara.models.requests import ListRequest, RunRequest
from capibara.models.responses import ListResponse, RunResponse, ScriptInfo
from capibara.sdk.client import CapibaraClient

__all__ = [
    "CapibaraClient",
    "RunRequest",
    "ListRequest",
    "RunResponse",
    "ListResponse",
    "ScriptInfo",
]
