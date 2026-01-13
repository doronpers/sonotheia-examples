"""
Tests for JSON safety utilities.
"""

import numpy as np

from audio_trust_harness.utils.json_safety import convert_numpy_types


def test_convert_simple_types():
    assert convert_numpy_types(1) == 1
    assert convert_numpy_types(1.5) == 1.5
    assert convert_numpy_types("test") == "test"
    assert convert_numpy_types(True) is True


def test_convert_numpy_scalars():
    assert isinstance(convert_numpy_types(np.int64(42)), int)
    assert isinstance(convert_numpy_types(np.float64(3.14)), float)
    assert isinstance(convert_numpy_types(np.bool_(True)), bool)

    assert convert_numpy_types(np.int64(42)) == 42
    assert convert_numpy_types(np.float64(3.14)) == 3.14


def test_convert_numpy_arrays():
    arr = np.array([1, 2, 3])
    converted = convert_numpy_types(arr)
    assert isinstance(converted, list)
    assert converted == [1, 2, 3]

    arr_2d = np.array([[1, 2], [3, 4]])
    converted_2d = convert_numpy_types(arr_2d)
    assert isinstance(converted_2d, list)
    assert converted_2d == [[1, 2], [3, 4]]


def test_convert_nested_structures():
    data = {
        "scalar": np.int32(10),
        "list": [np.float32(1.1), np.float32(2.2)],
        "array": np.array([100, 200]),
        "nested": {"val": np.bool_(False)},
    }

    converted = convert_numpy_types(data)

    assert isinstance(converted["scalar"], int)
    assert isinstance(converted["list"][0], float)
    assert isinstance(converted["array"], list)
    assert isinstance(converted["nested"]["val"], bool)
    assert converted["nested"]["val"] is False
