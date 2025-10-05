"""Validation utilities for Capibara Core."""

from typing import Any

from capibara.models.requests import ClearRequest, ListRequest, RunRequest, ShowRequest
from capibara.models.responses import (
    ClearResponse,
    ListResponse,
    RunResponse,
    ShowResponse,
)
from capibara.utils.logging import get_logger

logger = get_logger(__name__)


def validate_request(request: Any) -> bool:
    """Validate a request object."""
    try:
        if isinstance(request, RunRequest):
            return _validate_run_request(request)
        elif isinstance(request, ListRequest):
            return _validate_list_request(request)
        elif isinstance(request, ShowRequest):
            return _validate_show_request(request)
        elif isinstance(request, ClearRequest):
            return _validate_clear_request(request)
        else:
            logger.warning("Unknown request type", type=type(request).__name__)
            return False
    except Exception as e:
        logger.error("Request validation failed", error=str(e))
        return False


def validate_response(response: Any) -> bool:
    """Validate a response object."""
    try:
        if isinstance(response, RunResponse):
            return _validate_run_response(response)
        elif isinstance(response, ListResponse):
            return _validate_list_response(response)
        elif isinstance(response, ShowResponse):
            return _validate_show_response(response)
        elif isinstance(response, ClearResponse):
            return _validate_clear_response(response)
        else:
            logger.warning("Unknown response type", type=type(response).__name__)
            return False
    except Exception as e:
        logger.error("Response validation failed", error=str(e))
        return False


def _validate_run_request(request: RunRequest) -> bool:
    """Validate RunRequest."""
    if not request.prompt or not request.prompt.strip():
        logger.error("RunRequest validation failed: empty prompt")
        return False

    if not request.language:
        logger.error("RunRequest validation failed: missing language")
        return False

    # Validate language
    supported_languages = {"python", "javascript", "bash", "powershell"}
    if request.language.lower() not in supported_languages:
        logger.error(
            "RunRequest validation failed: unsupported language",
            language=request.language,
        )
        return False

    return True


def _validate_list_request(request: ListRequest) -> bool:
    """Validate ListRequest."""
    if request.limit <= 0 or request.limit > 1000:
        logger.error(
            "ListRequest validation failed: invalid limit", limit=request.limit
        )
        return False

    if request.offset < 0:
        logger.error(
            "ListRequest validation failed: negative offset", offset=request.offset
        )
        return False

    # Validate sort fields
    valid_sort_fields = {"created_at", "updated_at", "execution_count", "prompt_length"}
    if request.sort_by not in valid_sort_fields:
        logger.error(
            "ListRequest validation failed: invalid sort field", sort_by=request.sort_by
        )
        return False

    if request.sort_order not in {"asc", "desc"}:
        logger.error(
            "ListRequest validation failed: invalid sort order",
            sort_order=request.sort_order,
        )
        return False

    return True


def _validate_show_request(request: ShowRequest) -> bool:
    """Validate ShowRequest."""
    if not request.script_id or not request.script_id.strip():
        logger.error("ShowRequest validation failed: empty script_id")
        return False

    return True


def _validate_clear_request(request: ClearRequest) -> bool:
    """Validate ClearRequest."""
    # At least one clearing criteria must be specified
    if not any([request.script_ids, request.language, request.older_than, request.all]):
        logger.error("ClearRequest validation failed: no clearing criteria specified")
        return False

    # Validate script_ids if provided
    if request.script_ids is not None and len(request.script_ids) == 0:
        logger.error("ClearRequest validation failed: empty script_ids list")
        return False

    # Validate older_than if provided
    if request.older_than is not None and request.older_than <= 0:
        logger.error(
            "ClearRequest validation failed: invalid older_than",
            older_than=request.older_than,
        )
        return False

    return True


def _validate_run_response(response: RunResponse) -> bool:
    """Validate RunResponse."""
    if not response.script_id or not response.script_id.strip():
        logger.error("RunResponse validation failed: empty script_id")
        return False

    if not response.prompt or not response.prompt.strip():
        logger.error("RunResponse validation failed: empty prompt")
        return False

    if not response.language:
        logger.error("RunResponse validation failed: missing language")
        return False

    if not response.code or not response.code.strip():
        logger.error("RunResponse validation failed: empty code")
        return False

    if not response.llm_provider:
        logger.error("RunResponse validation failed: missing llm_provider")
        return False

    if not response.fingerprint:
        logger.error("RunResponse validation failed: missing fingerprint")
        return False

    return True


def _validate_list_response(response: ListResponse) -> bool:
    """Validate ListResponse."""
    if not isinstance(response.scripts, list):
        logger.error("ListResponse validation failed: scripts must be a list")
        return False

    if response.total_count < 0:
        logger.error(
            "ListResponse validation failed: negative total_count",
            total_count=response.total_count,
        )
        return False

    if response.limit <= 0:
        logger.error(
            "ListResponse validation failed: invalid limit", limit=response.limit
        )
        return False

    if response.offset < 0:
        logger.error(
            "ListResponse validation failed: negative offset", offset=response.offset
        )
        return False

    return True


def _validate_show_response(response: ShowResponse) -> bool:
    """Validate ShowResponse."""
    if not response.script:
        logger.error("ShowResponse validation failed: missing script")
        return False

    # Validate script object
    if not hasattr(response.script, "script_id") or not response.script.script_id:
        logger.error("ShowResponse validation failed: script missing script_id")
        return False

    return True


def _validate_clear_response(response: ClearResponse) -> bool:
    """Validate ClearResponse."""
    if response.cleared_count < 0:
        logger.error(
            "ClearResponse validation failed: negative cleared_count",
            cleared_count=response.cleared_count,
        )
        return False

    if not isinstance(response.cleared_script_ids, list):
        logger.error(
            "ClearResponse validation failed: cleared_script_ids must be a list"
        )
        return False

    if response.total_size_freed_bytes < 0:
        logger.error(
            "ClearResponse validation failed: negative total_size_freed_bytes",
            total_size_freed_bytes=response.total_size_freed_bytes,
        )
        return False

    return True


def validate_security_policy(policy_name: str, available_policies: list[str]) -> bool:
    """Validate that a security policy exists."""
    if policy_name and policy_name not in available_policies:
        logger.error(
            "Security policy validation failed: unknown policy",
            policy=policy_name,
            available=available_policies,
        )
        return False

    return True


def validate_llm_provider(provider_name: str, available_providers: list[str]) -> bool:
    """Validate that an LLM provider exists."""
    if provider_name and provider_name not in available_providers:
        logger.error(
            "LLM provider validation failed: unknown provider",
            provider=provider_name,
            available=available_providers,
        )
        return False

    return True


def validate_language(language: str) -> bool:
    """Validate programming language."""
    supported_languages = {"python", "javascript", "bash", "powershell"}
    if language.lower() not in supported_languages:
        logger.error(
            "Language validation failed: unsupported language",
            language=language,
            supported=supported_languages,
        )
        return False

    return True
