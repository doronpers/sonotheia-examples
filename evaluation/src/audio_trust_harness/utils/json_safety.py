"""Utilities for safe JSON serialization of numeric types."""

from typing import Any

import numpy as np


def convert_numpy_types(obj: Any) -> Any:
    """
    Recursively convert numpy types to native Python types for JSON serialization.

    Args:
        obj: The object to convert (dict, list, scalar, or other)

    Returns:
        The converted object with native Python types
    """
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return [convert_numpy_types(v) for v in obj.tolist()]
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    else:
        return obj
