"""
Tests for adapters.
"""

import numpy as np
import pytest

from audio_trust_harness.adapters import (
    AdapterResult,
    AdapterStatus,
    BaseAdapter,
    HTTPAdapter,
    HTTPAdapterConfig,
    LocalAdapter,
)


class TestLocalAdapter:
    """Tests for LocalAdapter."""

    def test_local_adapter_initialization(self):
        """Test LocalAdapter initializes correctly."""
        adapter = LocalAdapter()
        assert adapter.name == "local"
        assert adapter.is_available() is True

    def test_local_adapter_analyze_sine_wave(self):
        """Test LocalAdapter analyzes a simple sine wave."""
        adapter = LocalAdapter()

        # Generate 1 second of 440Hz sine wave
        sr = 16000
        t = np.linspace(0, 1.0, sr)
        audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)

        result = adapter.analyze(audio, sr)

        assert result.status == AdapterStatus.SUCCESS
        assert result.indicators is not None
        assert len(result.indicators) > 0

        # Check expected indicator keys
        expected_keys = [
            "spectral_centroid_mean",
            "spectral_centroid_std",
            "spectral_flatness_mean",
            "spectral_flatness_std",
            "spectral_rolloff_mean",
            "spectral_rolloff_std",
            "rms_energy",
            "crest_factor",
            "zero_crossing_rate",
        ]
        for key in expected_keys:
            assert key in result.indicators, f"Missing key: {key}"
            assert isinstance(result.indicators[key], float)

    def test_local_adapter_analyze_with_perturbation_name(self):
        """Test LocalAdapter includes perturbation in metadata."""
        adapter = LocalAdapter()
        sr = 16000
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1.0, sr)).astype(np.float32)

        result = adapter.analyze(audio, sr, perturbation_name="noise")

        assert result.status == AdapterStatus.SUCCESS
        assert result.metadata is not None
        assert result.metadata["perturbation"] == "noise"

    def test_local_adapter_analyze_silent_audio(self):
        """Test LocalAdapter handles silent audio."""
        adapter = LocalAdapter()
        sr = 16000
        audio = np.zeros(sr, dtype=np.float32)

        result = adapter.analyze(audio, sr)

        assert result.status == AdapterStatus.SUCCESS
        assert result.indicators is not None
        # Values should be valid (not NaN or Inf)
        for value in result.indicators.values():
            assert not np.isnan(value)
            assert not np.isinf(value)

    def test_local_adapter_get_info(self):
        """Test LocalAdapter get_info returns expected data."""
        adapter = LocalAdapter()
        info = adapter.get_info()

        assert info["name"] == "local"
        assert info["available"] is True
        assert info["type"] == "LocalAdapter"
        assert "indicators" in info
        assert len(info["indicators"]) == 6


class TestHTTPAdapter:
    """Tests for HTTPAdapter."""

    def test_http_adapter_config(self):
        """Test HTTPAdapterConfig defaults."""
        config = HTTPAdapterConfig(base_url="https://api.example.com/analyze")

        assert config.base_url == "https://api.example.com/analyze"
        assert config.api_key is None
        assert config.timeout_seconds == 30.0
        assert config.verify_ssl is True
        assert config.headers == {}

    def test_http_adapter_config_with_api_key(self):
        """Test HTTPAdapterConfig with API key."""
        config = HTTPAdapterConfig(
            base_url="https://api.example.com/analyze",
            api_key="test-key",
            timeout_seconds=60.0,
        )

        assert config.api_key == "test-key"
        assert config.timeout_seconds == 60.0

    def test_http_adapter_initialization(self):
        """Test HTTPAdapter initializes correctly."""
        config = HTTPAdapterConfig(base_url="https://api.example.com/analyze")
        adapter = HTTPAdapter(config)

        assert adapter.name == "http"
        assert adapter.config == config

    def test_http_adapter_get_info_hides_api_key(self):
        """Test HTTPAdapter get_info doesn't expose API key."""
        config = HTTPAdapterConfig(
            base_url="https://api.example.com/analyze",
            api_key="secret-key",
        )
        adapter = HTTPAdapter(config)
        info = adapter.get_info()

        assert info["base_url"] == "https://api.example.com/analyze"
        assert info["has_api_key"] is True
        assert "secret-key" not in str(info)

    def test_http_adapter_encode_audio(self):
        """Test HTTPAdapter audio encoding."""
        config = HTTPAdapterConfig(base_url="https://api.example.com/analyze")
        adapter = HTTPAdapter(config)

        sr = 16000
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 0.1, sr // 10)).astype(np.float32)

        encoded = adapter._encode_audio(audio, sr)

        # Should be base64 encoded
        assert isinstance(encoded, str)
        assert len(encoded) > 0

    def test_http_adapter_build_headers_without_api_key(self):
        """Test HTTPAdapter header building without API key."""
        config = HTTPAdapterConfig(base_url="https://api.example.com/analyze")
        adapter = HTTPAdapter(config)

        headers = adapter._build_headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        assert "Authorization" not in headers

    def test_http_adapter_build_headers_with_api_key(self):
        """Test HTTPAdapter header building with API key."""
        config = HTTPAdapterConfig(
            base_url="https://api.example.com/analyze",
            api_key="test-key",
        )
        adapter = HTTPAdapter(config)

        headers = adapter._build_headers()

        assert headers["Authorization"] == "Bearer test-key"

    def test_http_adapter_build_headers_with_custom_headers(self):
        """Test HTTPAdapter header building with custom headers."""
        config = HTTPAdapterConfig(
            base_url="https://api.example.com/analyze",
            headers={"X-Custom-Header": "custom-value"},
        )
        adapter = HTTPAdapter(config)

        headers = adapter._build_headers()

        assert headers["X-Custom-Header"] == "custom-value"

    def test_http_adapter_parse_response(self):
        """Test HTTPAdapter response parsing."""
        config = HTTPAdapterConfig(base_url="https://api.example.com/analyze")
        adapter = HTTPAdapter(config)

        response_data = {
            "indicators": {"test_indicator": 0.5},
            "deferral_action": "accept",
            "confidence": 0.95,
            "metadata": {"source": "api"},
        }

        result = adapter._parse_response(response_data)

        assert result.status == AdapterStatus.SUCCESS
        assert result.indicators == {"test_indicator": 0.5}
        assert result.deferral_action == "accept"
        assert result.confidence == 0.95
        assert result.metadata == {"source": "api"}

    def test_http_adapter_reset_availability(self):
        """Test HTTPAdapter availability reset."""
        config = HTTPAdapterConfig(base_url="https://api.example.com/analyze")
        adapter = HTTPAdapter(config)

        # Set cached value
        adapter._available = True
        assert adapter.is_available() is True

        # Reset and verify
        adapter.reset_availability()
        assert adapter._available is None


class TestAdapterResult:
    """Tests for AdapterResult dataclass."""

    def test_adapter_result_success(self):
        """Test AdapterResult for successful operation."""
        result = AdapterResult(
            status=AdapterStatus.SUCCESS,
            indicators={"test": 1.0},
        )

        assert result.status == AdapterStatus.SUCCESS
        assert result.indicators == {"test": 1.0}
        assert result.error_message is None

    def test_adapter_result_error(self):
        """Test AdapterResult for error."""
        result = AdapterResult(
            status=AdapterStatus.ERROR,
            error_message="Something went wrong",
        )

        assert result.status == AdapterStatus.ERROR
        assert result.indicators is None
        assert result.error_message == "Something went wrong"

    def test_adapter_result_rate_limited(self):
        """Test AdapterResult for rate limiting."""
        result = AdapterResult(
            status=AdapterStatus.RATE_LIMITED,
            error_message="Rate limit exceeded",
            metadata={"retry_after": "60"},
        )

        assert result.status == AdapterStatus.RATE_LIMITED
        assert result.metadata == {"retry_after": "60"}


class TestBaseAdapter:
    """Tests for BaseAdapter abstract class."""

    def test_base_adapter_is_abstract(self):
        """Test that BaseAdapter cannot be instantiated directly."""

        class IncompleteAdapter(BaseAdapter):
            pass

        with pytest.raises(TypeError):
            IncompleteAdapter("test")

    def test_custom_adapter_implementation(self):
        """Test creating a custom adapter implementation."""

        class MockAdapter(BaseAdapter):
            def analyze(self, audio_data, sample_rate, perturbation_name=None):
                return AdapterResult(
                    status=AdapterStatus.SUCCESS,
                    indicators={"mock": 42.0},
                )

            def is_available(self):
                return True

        adapter = MockAdapter("mock")
        assert adapter.name == "mock"
        assert adapter.is_available() is True

        result = adapter.analyze(np.zeros(100), 16000)
        assert result.indicators == {"mock": 42.0}
