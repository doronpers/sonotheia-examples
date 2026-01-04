"""
Tests for enhanced Sonotheia API client.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest
import requests

from client_enhanced import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    RateLimiter,
    SonotheiaClientEnhanced,
)


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("SONOTHEIA_API_KEY", "test-api-key")
    monkeypatch.setenv("SONOTHEIA_API_URL", "https://api.test.com")


@pytest.fixture
def client(mock_env):
    """Create test client."""
    return SonotheiaClientEnhanced(
        api_key="test-key",
        api_url="https://api.test.com",
        max_retries=2,
        rate_limit_rps=None,  # Disable rate limiting for tests
        enable_circuit_breaker=False,  # Disable circuit breaker for basic tests
    )


class TestCircuitBreaker:
    """Tests for circuit breaker functionality."""

    def test_initial_state_is_closed(self):
        """Circuit breaker should start in CLOSED state."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED

    def test_opens_after_threshold_failures(self):
        """Circuit breaker should open after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config)

        # Simulate failures
        for _ in range(3):
            cb._on_failure()

        assert cb.state == CircuitState.OPEN

    def test_call_blocks_when_open(self):
        """Circuit breaker should block calls when OPEN."""
        cb = CircuitBreaker()
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time()

        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            cb.call(lambda: None)

    def test_transitions_to_half_open_after_timeout(self):
        """Circuit breaker should transition to HALF_OPEN after recovery timeout."""
        config = CircuitBreakerConfig(recovery_timeout=0.1)
        cb = CircuitBreaker(config)
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time() - 0.2  # Past recovery timeout

        # Should transition to HALF_OPEN and succeed
        result = cb.call(lambda: "success")
        assert result == "success"
        assert cb.state == CircuitState.HALF_OPEN

    def test_closes_after_success_threshold_in_half_open(self):
        """Circuit breaker should close after success threshold in HALF_OPEN."""
        config = CircuitBreakerConfig(success_threshold=2)
        cb = CircuitBreaker(config)
        cb.state = CircuitState.HALF_OPEN

        # First success
        cb._on_success()
        assert cb.state == CircuitState.HALF_OPEN

        # Second success should close
        cb._on_success()
        assert cb.state == CircuitState.CLOSED

    def test_reopens_on_failure_in_half_open(self):
        """Circuit breaker should reopen on failure in HALF_OPEN state."""
        cb = CircuitBreaker()
        cb.state = CircuitState.HALF_OPEN

        cb._on_failure()
        assert cb.state == CircuitState.OPEN


class TestRateLimiter:
    """Tests for rate limiter functionality."""

    def test_acquires_tokens_immediately_when_available(self):
        """Rate limiter should acquire tokens immediately when available."""
        limiter = RateLimiter(requests_per_second=10.0)
        start = time.time()
        limiter.acquire(1)
        duration = time.time() - start
        assert duration < 0.1  # Should be nearly instant

    def test_blocks_when_tokens_exhausted(self):
        """Rate limiter should block when tokens exhausted."""
        limiter = RateLimiter(requests_per_second=2.0)

        # Acquire all tokens
        limiter.acquire(2)
        limiter.tokens = 0  # Force empty

        # Next acquire should block
        start = time.time()
        limiter.acquire(1)
        duration = time.time() - start
        assert duration >= 0.4  # Should wait for token refill


class TestSonotheiaClientEnhanced:
    """Tests for enhanced Sonotheia client."""

    def test_init_requires_api_key(self):
        """Client initialization should require API key."""
        with pytest.raises(ValueError, match="API key is required"):
            SonotheiaClientEnhanced(api_key=None)

    def test_init_from_env_var(self, mock_env):
        """Client should initialize from environment variable."""
        client = SonotheiaClientEnhanced()
        assert client.api_key == "test-api-key"
        assert client.api_url == "https://api.test.com"

    def test_session_created_with_retry_adapter(self, client):
        """Client should create session with retry adapter."""
        assert client.session is not None
        assert len(client.session.adapters) > 0

    def test_headers_include_auth(self, client):
        """Headers should include authorization."""
        headers = client._headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-key"

    @patch("client_enhanced.open", create=True)
    @patch("client_enhanced.requests.Session.request")
    def test_detect_deepfake_success(self, mock_request, mock_open, client):
        """Detect deepfake should succeed with valid response."""
        # Mock file open
        mock_file = MagicMock()
        mock_open.return_value.__enter__ = Mock(return_value=mock_file)
        mock_open.return_value.__exit__ = Mock()

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "score": 0.85,
            "label": "likely_synthetic",
            "latency_ms": 500,
        }
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        result = client.detect_deepfake("test.wav")

        assert result["score"] == 0.85
        assert result["label"] == "likely_synthetic"
        mock_request.assert_called_once()

    @patch("client_enhanced.open", create=True)
    @patch("client_enhanced.requests.Session.request")
    def test_verify_mfa_success(self, mock_request, mock_open, client):
        """Verify MFA should succeed with valid response."""
        mock_file = MagicMock()
        mock_open.return_value.__enter__ = Mock(return_value=mock_file)
        mock_open.return_value.__exit__ = Mock()

        mock_response = Mock()
        mock_response.json.return_value = {
            "verified": True,
            "enrollment_id": "enroll-123",
            "confidence": 0.95,
        }
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        result = client.verify_mfa("test.wav", "enroll-123")

        assert result["verified"] is True
        assert result["confidence"] == 0.95
        mock_request.assert_called_once()

    @patch("client_enhanced.requests.Session.request")
    def test_detect_deepfake_closes_file(self, mock_request, client, tmp_path):
        """Ensure enhanced client closes audio file handles."""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        audio_path = tmp_path / "audio.wav"
        audio_path.write_bytes(b"data")

        file_mock = mock_open(read_data=b"data")
        with patch("client_enhanced.open", file_mock, create=True):
            client.detect_deepfake(str(audio_path))

        assert file_mock.return_value.__exit__.call_count >= 1

    @patch("client_enhanced.requests.Session.request")
    def test_submit_sar_success(self, mock_request, client):
        """Submit SAR should succeed with valid response."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "submitted",
            "case_id": "case-123",
            "session_id": "session-123",
        }
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        result = client.submit_sar("session-123", "review", "Test reason")

        assert result["status"] == "submitted"
        assert result["case_id"] == "case-123"
        mock_request.assert_called_once()

    @patch("client_enhanced.requests.Session.request")
    def test_http_error_raises_exception(self, mock_request, client):
        """HTTP errors should be raised."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("API Error")
        mock_request.return_value = mock_response

        with pytest.raises(requests.HTTPError):
            client.submit_sar("session-123", "review", "Test")

    def test_context_manager(self, mock_env):
        """Client should work as context manager."""
        with SonotheiaClientEnhanced() as client:
            assert client.session is not None

        # Session should be closed after exit
        # Note: We can't directly test if session is closed,
        # but we verify the exit handler runs without error

    def test_circuit_breaker_enabled_by_default(self, mock_env):
        """Circuit breaker should be enabled by default."""
        client = SonotheiaClientEnhanced()
        assert client.circuit_breaker is not None

    def test_circuit_breaker_can_be_disabled(self, mock_env):
        """Circuit breaker can be disabled."""
        client = SonotheiaClientEnhanced(enable_circuit_breaker=False)
        assert client.circuit_breaker is None

    def test_rate_limiter_can_be_enabled(self, mock_env):
        """Rate limiter can be enabled."""
        client = SonotheiaClientEnhanced(rate_limit_rps=2.0)
        assert client.rate_limiter is not None
        assert client.rate_limiter.requests_per_second == 2.0
