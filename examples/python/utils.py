"""Shared utilities for Python examples."""

from __future__ import annotations

from typing import Any

try:
    import numpy as np
except ImportError:  # pragma: no cover - numpy may be optional for some usages
    np = None  # type: ignore[assignment]


def convert_numpy_types(obj: Any) -> Any:
    """
    Convert numpy scalars/arrays to native Python types for JSON serialization.

    Args:
        obj: Object to convert.

    Returns:
        JSON-serializable Python primitives and containers.
    """
    if np is not None:
        if isinstance(obj, np.generic):
            return obj.item()
        if isinstance(obj, np.ndarray):
            return [convert_numpy_types(v) for v in obj.tolist()]

    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(convert_numpy_types(v) for v in obj)

    return obj
