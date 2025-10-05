"""Fingerprinting utilities for content-addressable caching."""

import hashlib
import json
from typing import Any


def generate_fingerprint(
    prompt: str,
    language: str,
    context: dict[str, Any],
    security_policy: str = None,
    **kwargs: Any,
) -> str:
    """Generate a SHA-256 fingerprint for content-addressable caching."""
    # Create a deterministic representation of the input
    fingerprint_data = {
        "prompt": prompt.strip(),
        "language": language.lower(),
        "context": _normalize_context(context),
        "security_policy": security_policy,
        **kwargs,
    }

    # Convert to JSON string with sorted keys for consistency
    json_str = json.dumps(fingerprint_data, sort_keys=True, separators=(",", ":"))

    # Generate SHA-256 hash
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def _normalize_context(context: dict[str, Any]) -> dict[str, Any]:
    """Normalize context dictionary for consistent fingerprinting."""
    if not context:
        return {}

    # Sort keys and normalize values
    normalized = {}
    for key, value in sorted(context.items()):
        # Skip specific input values for caching - only include type information
        if key == "inputs" and isinstance(value, list):
            # Only include the count and types, not the actual values
            if len(value) > 0:
                input_types = []
                for input_val in value:
                    if isinstance(input_val, str):
                        try:
                            float(input_val)
                            input_types.append("number")
                        except ValueError:
                            input_types.append("string")
                    elif isinstance(input_val, (int, float)):
                        input_types.append("number")
                    elif isinstance(input_val, bool):
                        input_types.append("boolean")
                    else:
                        input_types.append("string")
                normalized[key] = {
                    "count": len(value),
                    "types": sorted(set(input_types)),
                }
        elif isinstance(value, dict):
            normalized[key] = _normalize_context(value)
        elif isinstance(value, list):
            normalized[key] = (
                sorted(value) if all(isinstance(x, str) for x in value) else value
            )
        else:
            normalized[key] = value

    return normalized


def generate_script_fingerprint(code: str, language: str) -> str:
    """Generate fingerprint for generated script code."""
    data = {
        "code": code.strip(),
        "language": language.lower(),
    }

    json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def generate_request_fingerprint(request_data: dict[str, Any]) -> str:
    """Generate fingerprint for a request."""
    # Remove non-deterministic fields
    fingerprint_data = {
        k: v
        for k, v in request_data.items()
        if k not in ["timestamp", "request_id", "session_id"]
    }

    json_str = json.dumps(fingerprint_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()
