"""
Tests for mock_api_server module.

This module tests the mock API server functionality.
"""

from __future__ import annotations

import json
from io import BytesIO

import pytest

# Check if Flask is available
try:
    from mock_api_server import MockConfig, app, check_rate_limit, verify_api_key

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    pytestmark = pytest.mark.skip("Flask not available")


@pytest.fixture
def client():
    """Create Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def mock_storage():
    """Create fresh mock storage for tests."""
    from mock_api_server import storage

    # Clear storage
    storage.clear()
    yield storage
    # Cleanup
    storage.clear()


class TestVerifyAPIKey:
    """Tests for verify_api_key function."""

    def test_verify_api_key_valid(self, client):
        """Test verification with valid API key."""
        with app.test_request_context(
            "/test", headers={"Authorization": "Bearer mock_api_key_12345"}
        ):
            valid, error = verify_api_key()
            assert valid is True
            assert error is None

    def test_verify_api_key_missing_header(self, client):
        """Test verification with missing Authorization header."""
        with app.test_request_context("/test"):
            valid, error = verify_api_key()
            assert valid is False
            assert error is not None

    def test_verify_api_key_invalid_key(self, client):
        """Test verification with invalid API key."""
        with app.test_request_context("/test", headers={"Authorization": "Bearer invalid_key"}):
            valid, error = verify_api_key()
            assert valid is False
            assert "Invalid" in error


class TestCheckRateLimit:
    """Tests for check_rate_limit function."""

    def test_check_rate_limit_allows_request(self, mock_storage):
        """Test that rate limit allows requests under limit."""
        allowed, headers = check_rate_limit("test-client")
        assert allowed is True
        assert "X-RateLimit-Limit" in headers

    def test_check_rate_limit_blocks_excessive_requests(self, mock_storage):
        """Test that rate limit blocks excessive requests."""
        # Make many requests to exceed limit
        config = MockConfig()
        for _ in range(config.rate_limit_per_minute + 1):
            allowed, _ = check_rate_limit("test-client")

        # Last request should be blocked
        assert allowed is False


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"


class TestDeepfakeEndpoint:
    """Tests for /v1/voice/deepfake endpoint."""

    def test_deepfake_endpoint_success(self, client, mock_storage):
        """Test successful deepfake detection."""
        audio_data = BytesIO(b"fake audio data" * 100)
        audio_data.name = "test.wav"

        response = client.post(
            "/v1/voice/deepfake",
            data={"audio": (audio_data, "test.wav")},
            headers={"Authorization": "Bearer mock_api_key_12345"},
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "score" in data
        assert "label" in data
        assert "latency_ms" in data
        assert 0 <= data["score"] <= 1

    def test_deepfake_endpoint_missing_audio(self, client):
        """Test deepfake endpoint with missing audio file."""
        response = client.post(
            "/v1/voice/deepfake",
            data={},
            headers={"Authorization": "Bearer mock_api_key_12345"},
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_deepfake_endpoint_authentication_required(self, client):
        """Test that authentication is required."""
        audio_data = BytesIO(b"fake audio data")
        audio_data.name = "test.wav"

        response = client.post(
            "/v1/voice/deepfake",
            data={"audio": (audio_data, "test.wav")},
        )

        assert response.status_code == 401

    def test_deepfake_endpoint_empty_file(self, client):
        """Test deepfake endpoint with empty audio file."""
        audio_data = BytesIO(b"")
        audio_data.name = "test.wav"

        response = client.post(
            "/v1/voice/deepfake",
            data={"audio": (audio_data, "test.wav")},
            headers={"Authorization": "Bearer mock_api_key_12345"},
        )

        assert response.status_code == 400


class TestMFAEndpoint:
    """Tests for /v1/mfa/voice/verify endpoint."""

    def test_mfa_endpoint_success(self, client, mock_storage):
        """Test successful MFA verification."""
        audio_data = BytesIO(b"fake audio data" * 100)
        audio_data.name = "test_match.wav"

        response = client.post(
            "/v1/mfa/voice/verify",
            data={
                "audio": (audio_data, "test_match.wav"),
                "enrollment_id": "enroll-123",
            },
            headers={"Authorization": "Bearer mock_api_key_12345"},
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "verified" in data
        assert "enrollment_id" in data
        assert "confidence" in data
        assert isinstance(data["verified"], bool)

    def test_mfa_endpoint_missing_enrollment_id(self, client):
        """Test MFA endpoint with missing enrollment_id."""
        audio_data = BytesIO(b"fake audio data")
        audio_data.name = "test.wav"

        response = client.post(
            "/v1/mfa/voice/verify",
            data={"audio": (audio_data, "test.wav")},
            headers={"Authorization": "Bearer mock_api_key_12345"},
        )

        assert response.status_code == 400


class TestSAREndpoint:
    """Tests for /v1/reports/sar endpoint."""

    def test_sar_endpoint_success(self, client, mock_storage):
        """Test successful SAR submission."""
        response = client.post(
            "/v1/reports/sar",
            json={
                "session_id": "session-123",
                "decision": "review",
                "reason": "Test reason",
            },
            headers={"Authorization": "Bearer mock_api_key_12345"},
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "status" in data
        assert "case_id" in data
        assert "session_id" in data

    def test_sar_endpoint_missing_fields(self, client):
        """Test SAR endpoint with missing required fields."""
        response = client.post(
            "/v1/reports/sar",
            json={"session_id": "session-123"},
            headers={"Authorization": "Bearer mock_api_key_12345"},
        )

        assert response.status_code == 400


class TestMockConfigEndpoint:
    """Tests for /mock/config endpoint."""

    def test_mock_config_get(self, client):
        """Test getting mock configuration."""
        response = client.get("/mock/config")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "deepfake_latency_ms" in data

    def test_mock_config_post(self, client):
        """Test updating mock configuration."""
        response = client.post(
            "/mock/config",
            json={"always_succeed": True, "deepfake_latency_ms": 100},
        )
        assert response.status_code == 200


class TestMockStatsEndpoint:
    """Tests for /mock/stats endpoint."""

    def test_mock_stats(self, client, mock_storage):
        """Test getting mock server statistics."""
        response = client.get("/mock/stats")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "total_sessions" in data
        assert "total_enrollments" in data


class TestMockResetEndpoint:
    """Tests for /mock/reset endpoint."""

    def test_mock_reset(self, client, mock_storage):
        """Test resetting mock server state."""
        # Add some data
        mock_storage.sessions["test-session"] = {"data": "test"}

        response = client.post("/mock/reset")
        assert response.status_code == 200

        # Verify storage is cleared
        assert len(mock_storage.sessions) == 0


class TestErrorSimulation:
    """Tests for error simulation functionality."""

    def test_error_simulation(self, client):
        """Test that error simulation can be configured."""
        # Configure to always return errors
        client.post("/mock/config", json={"simulate_errors": True, "error_rate": 1.0})

        audio_data = BytesIO(b"fake audio data" * 100)
        audio_data.name = "test.wav"

        response = client.post(
            "/v1/voice/deepfake",
            data={"audio": (audio_data, "test.wav")},
            headers={"Authorization": "Bearer mock_api_key_12345"},
        )

        # Should return an error
        assert response.status_code >= 400

        # Reset to normal operation
        client.post("/mock/config", json={"simulate_errors": False})
