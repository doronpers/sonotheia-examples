"""Unit tests for Sonotheia API client."""

from unittest.mock import Mock, mock_open, patch

import pytest
import requests

from client import SonotheiaClient


class TestSonotheiaClient:
    """Test cases for SonotheiaClient."""

    def test_init_with_api_key(self):
        """Test client initialization with explicit API key."""
        client = SonotheiaClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.api_url == "https://api.sonotheia.com"

    def test_init_without_api_key(self):
        """Test client initialization without API key raises ValueError."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key is required"):
                SonotheiaClient()

    def test_init_with_env_vars(self):
        """Test client initialization with environment variables."""
        env = {
            "SONOTHEIA_API_KEY": "env-key",
            "SONOTHEIA_API_URL": "https://custom.api.com",
            "SONOTHEIA_DEEPFAKE_PATH": "/custom/deepfake",
        }
        with patch.dict("os.environ", env, clear=True):
            client = SonotheiaClient()
            assert client.api_key == "env-key"
            assert client.api_url == "https://custom.api.com"
            assert client.deepfake_path == "/custom/deepfake"

    def test_init_strips_trailing_slash(self):
        """Test that API URL trailing slash is stripped."""
        client = SonotheiaClient(api_key="test", api_url="https://api.example.com/")
        assert client.api_url == "https://api.example.com"

    def test_headers(self):
        """Test _headers method returns correct authorization header."""
        client = SonotheiaClient(api_key="test-key")
        headers = client._headers()
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["Accept"] == "application/json"

    @patch("client.mimetypes.guess_type", return_value=("audio/wav", None))
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake audio data")
    @patch("requests.post")
    def test_detect_deepfake_success(self, mock_post, mock_file, mock_mime):
        """Test successful deepfake detection."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "score": 0.85,
            "label": "likely_synthetic",
            "latency_ms": 640,
        }
        mock_post.return_value = mock_response

        client = SonotheiaClient(api_key="test-key")
        result = client.detect_deepfake("test.wav", metadata={"session_id": "test-123"})

        # Verify result
        assert result["score"] == 0.85
        assert result["label"] == "likely_synthetic"

        # Verify API call
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["headers"]["Authorization"] == "Bearer test-key"
        assert "metadata" in call_kwargs["data"]

    @patch("client.mimetypes.guess_type", return_value=("audio/wav", None))
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake audio data")
    @patch("requests.post")
    def test_detect_deepfake_http_error(self, mock_post, mock_file, mock_mime):
        """Test deepfake detection with HTTP error."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.HTTPError("Bad Request")
        mock_post.return_value = mock_response

        client = SonotheiaClient(api_key="test-key")

        with pytest.raises(requests.HTTPError):
            client.detect_deepfake("test.wav")

    @patch("client.mimetypes.guess_type", return_value=("audio/wav", None))
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake audio data")
    @patch("requests.post")
    def test_verify_mfa_success(self, mock_post, mock_file, mock_mime):
        """Test successful MFA verification."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "verified": True,
            "enrollment_id": "enroll-123",
            "confidence": 0.93,
        }
        mock_post.return_value = mock_response

        client = SonotheiaClient(api_key="test-key")
        result = client.verify_mfa("test.wav", "enroll-123", context={"channel": "ivr"})

        # Verify result
        assert result["verified"] is True
        assert result["confidence"] == 0.93

        # Verify API call
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["data"]["enrollment_id"] == "enroll-123"

    @patch("client.mimetypes.guess_type", return_value=("audio/wav", None))
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake audio data")
    @patch("requests.post")
    def test_verify_mfa_failed(self, mock_post, mock_file, mock_mime):
        """Test MFA verification failure."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "verified": False,
            "enrollment_id": "enroll-123",
            "confidence": 0.25,
        }
        mock_post.return_value = mock_response

        client = SonotheiaClient(api_key="test-key")
        result = client.verify_mfa("test.wav", "enroll-123")

        assert result["verified"] is False

    @patch("requests.post")
    def test_submit_sar_success(self, mock_post):
        """Test successful SAR submission."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "submitted",
            "case_id": "sar-001234",
            "session_id": "session-123",
        }
        mock_post.return_value = mock_response

        client = SonotheiaClient(api_key="test-key")
        result = client.submit_sar(
            "session-123", "review", "Suspicious activity", metadata={"source": "test"}
        )

        # Verify result
        assert result["status"] == "submitted"
        assert result["case_id"] == "sar-001234"

        # Verify API call
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["json"]["session_id"] == "session-123"
        assert call_kwargs["json"]["decision"] == "review"

    @patch("requests.post")
    def test_submit_sar_with_all_decisions(self, mock_post):
        """Test SAR submission with different decision types."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "submitted",
            "case_id": "sar-001234",
            "session_id": "session-123",
        }
        mock_post.return_value = mock_response

        client = SonotheiaClient(api_key="test-key")

        for decision in ["allow", "deny", "review"]:
            client.submit_sar("session-123", decision, "Test reason")
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["json"]["decision"] == decision

    @patch("requests.post")
    def test_timeout_configuration(self, mock_post):
        """Test that custom timeout is used."""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        client = SonotheiaClient(api_key="test-key", timeout=60)
        client.submit_sar("session-123", "review", "Test")

        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["timeout"] == 60

    def test_custom_endpoint_paths(self):
        """Test client with custom endpoint paths."""
        client = SonotheiaClient(
            api_key="test-key",
            deepfake_path="/custom/deepfake",
            mfa_path="/custom/mfa",
            sar_path="/custom/sar",
        )

        assert client.deepfake_path == "/custom/deepfake"
        assert client.mfa_path == "/custom/mfa"
        assert client.sar_path == "/custom/sar"


class TestClientIntegration:
    """Integration-style tests without mocking HTTP."""

    def test_client_construction_with_defaults(self):
        """Test that client can be constructed with minimal config."""
        with patch.dict("os.environ", {"SONOTHEIA_API_KEY": "test-key"}, clear=True):
            client = SonotheiaClient()
            assert client.api_key == "test-key"
            assert client.api_url == "https://api.sonotheia.com"
            assert client.timeout == 30

    def test_error_handling_for_missing_file(self):
        """Test error handling when audio file doesn't exist."""
        client = SonotheiaClient(api_key="test-key")

        with pytest.raises(FileNotFoundError):
            client.detect_deepfake("/nonexistent/file.wav")
