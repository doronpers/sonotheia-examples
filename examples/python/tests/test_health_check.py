"""
Tests for health_check module.

This module tests the health check functionality.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import requests

from health_check import HealthCheckResult, SonotheiaHealthChecker


class TestHealthCheckResult:
    """Tests for HealthCheckResult dataclass."""

    def test_health_check_result_creation(self):
        """Test that HealthCheckResult can be created."""
        result = HealthCheckResult(
            timestamp="2024-01-01T00:00:00Z",
            healthy=True,
            latency_ms=100.5,
            status_code=200,
        )

        assert result.healthy is True
        assert result.latency_ms == 100.5
        assert result.status_code == 200
        assert result.error is None

    def test_health_check_result_with_error(self):
        """Test HealthCheckResult with error."""
        result = HealthCheckResult(
            timestamp="2024-01-01T00:00:00Z",
            healthy=False,
            latency_ms=50.0,
            error="Connection failed",
        )

        assert result.healthy is False
        assert result.error == "Connection failed"


class TestSonotheiaHealthChecker:
    """Tests for SonotheiaHealthChecker class."""

    def test_init(self):
        """Test health checker initialization."""
        checker = SonotheiaHealthChecker(api_key="test-key")
        assert checker.api_key == "test-key"
        assert checker.api_url == "https://api.sonotheia.com"
        assert checker.timeout == 10

    def test_init_with_custom_url(self):
        """Test health checker with custom URL."""
        checker = SonotheiaHealthChecker(api_key="test-key", api_url="https://custom.api.com")
        assert checker.api_url == "https://custom.api.com"

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from URL."""
        checker = SonotheiaHealthChecker(api_key="test-key", api_url="https://api.example.com/")
        assert checker.api_url == "https://api.example.com"

    @patch("health_check.requests.get")
    def test_health_check_success(self, mock_get):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_get.return_value = mock_response

        checker = SonotheiaHealthChecker(api_key="test-key")
        result = checker.check_connectivity()

        assert result.healthy is True
        assert result.status_code == 200
        assert result.latency_ms >= 0
        assert result.error is None

    @patch("health_check.requests.get")
    def test_health_check_api_unavailable(self, mock_get):
        """Test health check when API is unavailable."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        checker = SonotheiaHealthChecker(api_key="test-key")
        result = checker.check_connectivity()

        assert result.healthy is False
        assert result.error is not None
        assert "Connection" in result.error or "failed" in result.error.lower()

    @patch("health_check.requests.get")
    def test_health_check_invalid_api_key(self, mock_get):
        """Test health check with invalid API key."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.HTTPError("Unauthorized")
        mock_get.return_value = mock_response

        checker = SonotheiaHealthChecker(api_key="invalid-key")
        result = checker.check_connectivity()

        assert result.healthy is False
        assert result.status_code == 401

    @patch("health_check.requests.get")
    def test_health_check_timeout(self, mock_get):
        """Test health check timeout handling."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")

        checker = SonotheiaHealthChecker(api_key="test-key", timeout=1)
        result = checker.check_connectivity()

        assert result.healthy is False
        assert result.error is not None
        assert "timeout" in result.error.lower()

    @patch("health_check.requests.get")
    def test_health_check_metrics_collection(self, mock_get):
        """Test that health check collects latency metrics."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_get.return_value = mock_response

        checker = SonotheiaHealthChecker(api_key="test-key")
        result = checker.check_connectivity()

        assert result.latency_ms >= 0
        assert isinstance(result.latency_ms, float)

    @patch("health_check.requests.get")
    def test_health_check_non_200_status(self, mock_get):
        """Test health check with non-200 status code."""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.json.return_value = {"status": "degraded"}
        mock_get.return_value = mock_response

        checker = SonotheiaHealthChecker(api_key="test-key")
        result = checker.check_connectivity()

        assert result.healthy is False
        assert result.status_code == 503
