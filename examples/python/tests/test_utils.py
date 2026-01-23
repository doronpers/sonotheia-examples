"""
Tests for utils module.

This module tests the utility functions used across the Sonotheia Python examples.
"""

from __future__ import annotations

import pytest


class TestConvertNumpyTypes:
    """Tests for convert_numpy_types function."""

    def test_with_primitive_types(self):
        """Test that primitive types are returned unchanged."""
        from utils import convert_numpy_types

        assert convert_numpy_types(42) == 42
        assert convert_numpy_types(3.14) == 3.14
        assert convert_numpy_types("hello") == "hello"
        assert convert_numpy_types(True) is True
        assert convert_numpy_types(None) is None

    def test_with_dict(self):
        """Test conversion with dictionary."""
        from utils import convert_numpy_types

        data = {"a": 1, "b": 2, "c": "test"}
        result = convert_numpy_types(data)
        assert result == {"a": 1, "b": 2, "c": "test"}
        assert isinstance(result, dict)

    def test_with_list(self):
        """Test conversion with list."""
        from utils import convert_numpy_types

        data = [1, 2, 3, "test"]
        result = convert_numpy_types(data)
        assert result == [1, 2, 3, "test"]
        assert isinstance(result, list)

    def test_with_tuple(self):
        """Test conversion with tuple."""
        from utils import convert_numpy_types

        data = (1, 2, 3)
        result = convert_numpy_types(data)
        assert result == (1, 2, 3)
        assert isinstance(result, tuple)

    def test_with_nested_structures(self):
        """Test conversion with nested structures."""
        from utils import convert_numpy_types

        data = {
            "list": [1, 2, {"nested": "value"}],
            "dict": {"key": [1, 2, 3]},
            "tuple": (1, 2, 3),
        }
        result = convert_numpy_types(data)
        assert result == {
            "list": [1, 2, {"nested": "value"}],
            "dict": {"key": [1, 2, 3]},
            "tuple": (1, 2, 3),
        }

    def test_with_numpy_scalar(self):
        """Test conversion with numpy scalar."""
        try:
            import numpy as np
        except ImportError:
            pytest.skip("numpy not available")

        from utils import convert_numpy_types

        # Test various numpy scalar types
        assert convert_numpy_types(np.int32(42)) == 42
        assert convert_numpy_types(np.int64(42)) == 42
        assert convert_numpy_types(np.float32(3.14)) == pytest.approx(3.14)
        assert convert_numpy_types(np.float64(3.14)) == pytest.approx(3.14)
        assert convert_numpy_types(np.bool_(True)) is True

    def test_with_numpy_array(self):
        """Test conversion with numpy array."""
        try:
            import numpy as np
        except ImportError:
            pytest.skip("numpy not available")

        from utils import convert_numpy_types

        arr = np.array([1, 2, 3, 4, 5])
        result = convert_numpy_types(arr)
        assert result == [1, 2, 3, 4, 5]
        assert isinstance(result, list)

        # Test 2D array
        arr_2d = np.array([[1, 2], [3, 4]])
        result_2d = convert_numpy_types(arr_2d)
        assert result_2d == [[1, 2], [3, 4]]

    def test_with_nested_numpy_structures(self):
        """Test conversion with nested numpy structures."""
        try:
            import numpy as np
        except ImportError:
            pytest.skip("numpy not available")

        from utils import convert_numpy_types

        data = {
            "scalar": np.int32(42),
            "array": np.array([1, 2, 3]),
            "nested": {
                "value": np.float64(3.14),
                "list": [np.int32(1), np.int32(2)],
            },
        }
        result = convert_numpy_types(data)
        assert result == {
            "scalar": 42,
            "array": [1, 2, 3],
            "nested": {"value": pytest.approx(3.14), "list": [1, 2]},
        }

    def test_without_numpy(self, monkeypatch):
        """Test that function works when numpy is not available."""
        # Simulate numpy not being available
        import sys

        numpy_backup = sys.modules.get("numpy")
        if "numpy" in sys.modules:
            del sys.modules["numpy"]
        if "utils" in sys.modules:
            del sys.modules["utils"]

        from utils import convert_numpy_types

        # Should work fine with regular Python types
        assert convert_numpy_types({"a": 1, "b": 2}) == {"a": 1, "b": 2}
        assert convert_numpy_types([1, 2, 3]) == [1, 2, 3]

        # Restore numpy if it was there
        if numpy_backup:
            sys.modules["numpy"] = numpy_backup

    def test_with_empty_structures(self):
        """Test conversion with empty structures."""
        from utils import convert_numpy_types

        assert convert_numpy_types({}) == {}
        assert convert_numpy_types([]) == []
        assert convert_numpy_types(()) == ()

    def test_with_mixed_types_in_list(self):
        """Test conversion with mixed types in a list."""
        from utils import convert_numpy_types

        data = [1, "string", 3.14, True, None, {"key": "value"}]
        result = convert_numpy_types(data)
        assert result == [1, "string", 3.14, True, None, {"key": "value"}]
