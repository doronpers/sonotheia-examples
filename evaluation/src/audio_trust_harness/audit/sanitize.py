"""
Audit record sanitization to ensure public-safe output.

Enforces that audit records contain no raw audio bytes, base64-encoded data,
or large arrays that could leak sensitive information.
"""

import base64
from typing import Any


def sanitize_audit_record(data: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize audit record to ensure public-safe output.

    Removes or replaces any fields that contain:
    - Raw audio bytes
    - Base64-encoded data
    - Large arrays (>100 elements)
    - Binary data

    Args:
        data: Audit record dictionary

    Returns:
        Sanitized audit record dictionary
    """
    sanitized: dict[str, Any] = {}
    forbidden_keys = {
        "audio_bytes",
        "raw_audio",
        "audio_data",
        "base64",
        "base64_data",
        "binary",
        "binary_data",
    }

    for key, value in data.items():
        # Skip forbidden keys
        if any(forbidden in key.lower() for forbidden in forbidden_keys):
            continue

        # Recursively sanitize nested structures
        if isinstance(value, dict):
            sanitized[key] = sanitize_audit_record(value)
        elif isinstance(value, list):
            sanitized[key] = sanitize_list(value)
        elif isinstance(value, str):
            # Check for base64-like strings
            if is_base64_like(value):
                sanitized[key] = "[REDACTED: base64-like data]"
            else:
                sanitized[key] = value
        elif isinstance(value, (bytes, bytearray)):
            # Remove binary data
            continue
        else:
            sanitized[key] = value

    return sanitized


def sanitize_list(items: list[Any]) -> list[Any]:
    """
    Sanitize list items.

    Args:
        items: List to sanitize

    Returns:
        Sanitized list
    """
    sanitized: list[Any] = []
    for item in items:
        if isinstance(item, dict):
            sanitized.append(sanitize_audit_record(item))
        elif isinstance(item, list):
            sanitized.append(sanitize_list(item))
        elif isinstance(item, str):
            if is_base64_like(item):
                sanitized.append("[REDACTED: base64-like data]")
            else:
                sanitized.append(item)
        elif isinstance(item, (bytes, bytearray)):
            # Skip binary data
            continue
        elif isinstance(item, (int, float, bool, type(None))):
            sanitized.append(item)
        else:
            # For other types, try to convert to string or skip
            try:
                # Check if it's a large array-like object
                if hasattr(item, "__len__") and len(item) > 100:
                    sanitized.append(f"[REDACTED: large array ({len(item)} elements)]")
                else:
                    sanitized.append(item)
            except (TypeError, AttributeError):
                sanitized.append(item)

    return sanitized


def is_base64_like(value: str) -> bool:
    """
    Check if a string looks like base64-encoded data.

    Args:
        value: String to check

    Returns:
        True if string appears to be base64-encoded
    """
    if not isinstance(value, str) or len(value) < 20:
        return False

    # Base64 strings are typically long and contain only base64 characters
    base64_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")

    # Check if all characters are base64 characters
    if not all(c in base64_chars for c in value):
        return False

    # Check if it ends with padding (common in base64)
    if value.endswith("=") or value.endswith("=="):
        return True

    # Check if it's long enough and has high base64 character density
    if len(value) > 100:
        # Try to decode it (if it decodes, it's likely base64)
        try:
            base64.b64decode(value, validate=True)
            return True
        except Exception:
            pass

    return False


def validate_no_forbidden_fields(data: dict[str, Any]) -> bool:
    """
    Validate that audit record contains no forbidden fields.

    Args:
        data: Audit record dictionary

    Returns:
        True if record is valid (no forbidden fields), False otherwise
    """
    forbidden_patterns = [
        "audio_bytes",
        "raw_audio",
        "audio_data",
        "base64",
        "binary",
    ]

    def check_recursive(obj: Any, path: str = "") -> bool:
        """Recursively check for forbidden fields."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                key_lower = key.lower()
                if any(pattern in key_lower for pattern in forbidden_patterns):
                    return False
                if not check_recursive(value, f"{path}.{key}"):
                    return False
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if not check_recursive(item, f"{path}[{i}]"):
                    return False
        elif isinstance(obj, str):
            if is_base64_like(obj):
                return False
        elif isinstance(obj, (bytes, bytearray)):
            return False

        return True

    return check_recursive(data)
