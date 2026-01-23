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
        # Default URL is now http://localhost:8000 if not set via env var
        assert client.api_url == "http://localhost:8000"

    def test_init_without_api_key(self):
        """Test client initialization without API key (now allowed for demo usage)."""
        with patch.dict("os.environ", {}, clear=True):
            # Client now allows None API key for demo usage
            client = SonotheiaClient()
            assert client.api_key is None

    def test_init_with_env_vars(self):
        """Test client initialization with environment variables."""
        env = {
            "SONOTHEIA_API_KEY": "env-key",
            "SONOTHEIA_API_URL": "https://custom.api.com",
        }
        with patch.dict("os.environ", env, clear=True):
            client = SonotheiaClient()
            assert client.api_key == "env-key"
            assert client.api_url == "https://custom.api.com"
            # deepfake_path is not configurable via env var, uses default
            assert client.deepfake_path == "/api/detect"

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

    @patch("client.os.path.exists", return_value=True)
    @patch("client.mimetypes.guess_type", return_value=("audio/wav", None))
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake audio data")
    @patch("requests.post")
    def test_detect_deepfake_success(self, mock_post, mock_file, mock_mime, mock_exists):
        """Test successful deepfake detection."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "score": 0.85,
            "label": "likely_synthetic",
            "latency_ms": 640,
        }
        mock_response.raise_for_status = Mock()
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
        assert "params" in call_kwargs
        assert call_kwargs["params"]["quick_mode"] == "false"

    @patch("client.os.path.exists", return_value=True)
    @patch("client.mimetypes.guess_type", return_value=("audio/wav", None))
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake audio data")
    @patch("requests.post")
    def test_detect_deepfake_http_error(self, mock_post, mock_file, mock_mime, mock_exists):
        """Test deepfake detection with HTTP error."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.HTTPError("Bad Request")
        mock_post.return_value = mock_response

        client = SonotheiaClient(api_key="test-key")

        with pytest.raises(requests.HTTPError):
            client.detect_deepfake("test.wav")

    @patch("client.os.path.exists", return_value=True)
    @patch("client.mimetypes.guess_type", return_value=("audio/wav", None))
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake audio data")
    @patch("requests.post")
    def test_verify_mfa_success(self, mock_post, mock_file, mock_mime, mock_exists):
        """Test successful MFA verification."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "verified": True,
            "enrollment_id": "enroll-123",
            "confidence": 0.93,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = SonotheiaClient(api_key="test-key")
        # verify_mfa now requires transaction_id and customer_id
        result = client.verify_mfa("test.wav", "txn-123", "cust-456", context={"channel": "ivr"})

        # Verify result
        assert result["verified"] is True
        assert result["confidence"] == 0.93

        # Verify API call
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["json"]["transaction_id"] == "txn-123"
        assert call_kwargs["json"]["customer_id"] == "cust-456"

    @patch("client.os.path.exists", return_value=True)
    @patch("client.mimetypes.guess_type", return_value=("audio/wav", None))
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake audio data")
    @patch("requests.post")
    def test_verify_mfa_failed(self, mock_post, mock_file, mock_mime, mock_exists):
        """Test MFA verification failure."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "verified": False,
            "enrollment_id": "enroll-123",
            "confidence": 0.25,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = SonotheiaClient(api_key="test-key")
        # verify_mfa now requires transaction_id and customer_id
        result = client.verify_mfa("test.wav", "txn-123", "cust-456")

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
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = SonotheiaClient(api_key="test-key")
        # submit_sar now requires transaction_id, customer_id, activity_type, description
        result = client.submit_sar(
            "txn-123",
            "cust-456",
            "suspicious_activity",
            "Suspicious activity",
            metadata={"source": "test"},
        )

        # Verify result
        assert result["status"] == "submitted"
        assert result["case_id"] == "sar-001234"

        # Verify API call
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["json"]["transaction_id"] == "txn-123"
        assert call_kwargs["json"]["customer_id"] == "cust-456"
        assert call_kwargs["json"]["activity_type"] == "suspicious_activity"

    @patch("requests.post")
    def test_submit_sar_with_all_decisions(self, mock_post):
        """Test SAR submission with different decision types."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "submitted",
            "case_id": "sar-001234",
            "session_id": "session-123",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = SonotheiaClient(api_key="test-key")

        for activity_type in ["suspicious_activity", "fraud", "money_laundering"]:
            client.submit_sar("txn-123", "cust-456", activity_type, "Test reason")
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["json"]["activity_type"] == activity_type

    @patch("requests.post")
    def test_timeout_configuration(self, mock_post):
        """Test that custom timeout is used."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "submitted",
            "case_id": "case-123",
            "session_id": "session-123",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = SonotheiaClient(api_key="test-key", timeout=60)
        # submit_sar now requires transaction_id, customer_id, activity_type, description
        client.submit_sar("txn-123", "cust-456", "suspicious_activity", "Test description")

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

    @patch("client.requests.post")
    def test_detect_deepfake_closes_file(self, mock_post, tmp_path):
        """Ensure audio file handles are closed after deepfake call."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "score": 0.5,
            "label": "likely_real",
            "latency_ms": 100,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        audio_path = tmp_path / "audio.wav"
        audio_path.write_bytes(b"data")

        file_mock = mock_open(read_data=b"data")
        with patch("builtins.open", file_mock):
            SonotheiaClient(api_key="test-key").detect_deepfake(str(audio_path))

        assert file_mock.return_value.__exit__.call_count >= 1


class TestClientIntegration:
    """Integration-style tests without mocking HTTP."""

    def test_client_construction_with_defaults(self):
        """Test that client can be constructed with minimal config."""
        with patch.dict("os.environ", {"SONOTHEIA_API_KEY": "test-key"}, clear=True):
            client = SonotheiaClient()
            assert client.api_key == "test-key"
            # Default URL is now http://localhost:8000 if not set via env var
            assert client.api_url == "http://localhost:8000"
            assert client.timeout == 30

    def test_error_handling_for_missing_file(self):
        """Test error handling when audio file doesn't exist."""
        client = SonotheiaClient(api_key="test-key")

        with pytest.raises(FileNotFoundError):
            client.detect_deepfake("/nonexistent/file.wav")

    @patch("client.os.path.exists", return_value=True)
    @patch("client.mimetypes.guess_type", return_value=(None, None))
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake audio data")
    @patch("requests.post")
    def test_audio_part_fallback_mime_type(self, mock_post, mock_file, mock_mime, mock_exists):
        """Test that _audio_part uses fallback MIME type when mimetypes fails."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "score": 0.5,
            "label": "likely_real",
            "latency_ms": 100,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = SonotheiaClient(api_key="test-key")
        result = client.detect_deepfake("test.wav")

        assert result["score"] == 0.5
        mock_post.assert_called_once()

    @patch("client.os.path.exists", return_value=True)
    @patch("client.mimetypes.guess_type", return_value=("audio/wav", None))
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake audio data")
    @patch("requests.post")
    def test_response_validation_enabled(self, mock_post, mock_file, mock_mime, mock_exists):
        """Test that response validation works when enabled."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "score": 0.5,
            "label": "likely_real",
            "latency_ms": 100,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = SonotheiaClient(api_key="test-key", validate_responses=True)
        result = client.detect_deepfake("test.wav")

        assert result["score"] == 0.5
        assert "label" in result

    @patch("client.os.path.exists", return_value=True)
    @patch("client.mimetypes.guess_type", return_value=("audio/wav", None))
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake audio data")
    @patch("requests.post")
    def test_response_validation_disabled(self, mock_post, mock_file, mock_mime, mock_exists):
        """Test that response validation can be disabled."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "score": 0.5,
            "label": "likely_real",
            "latency_ms": 100,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = SonotheiaClient(api_key="test-key", validate_responses=False)
        result = client.detect_deepfake("test.wav")

        assert result["score"] == 0.5
        assert client.validator is None

    @patch("client.os.path.exists", return_value=True)
    @patch("client.mimetypes.guess_type", return_value=("audio/wav", None))
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake audio data")
    @patch("requests.post")
    def test_verify_mfa_with_validation_error(self, mock_post, mock_file, mock_mime, mock_exists):
        """Test that MFA verification continues even if validation fails."""
        from response_validator import ResponseValidationError

        mock_response = Mock()
        mock_response.json.return_value = {
            "verified": True,
            "enrollment_id": "enroll-123",
            "confidence": 0.9,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = SonotheiaClient(api_key="test-key", validate_responses=True)
        # Mock validator to raise an error
        with patch.object(
            client.validator, "validate_mfa_response", side_effect=ResponseValidationError("Test")
        ):
            # verify_mfa now requires transaction_id and customer_id
            result = client.verify_mfa("test.wav", "txn-123", "cust-456")
            # Should still return result despite validation error
            assert "verified" in result

    @patch("requests.post")
    def test_submit_sar_with_validation_error(self, mock_post):
        """Test that SAR submission continues even if validation fails."""
        from response_validator import ResponseValidationError

        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "submitted",
            "case_id": "case-123",
            "session_id": "session-123",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = SonotheiaClient(api_key="test-key", validate_responses=True)
        # Mock validator to raise an error
        with patch.object(
            client.validator, "validate_sar_response", side_effect=ResponseValidationError("Test")
        ):
            result = client.submit_sar("txn-123", "cust-456", "suspicious_activity", "Test reason")
            # Should still return result despite validation error
            assert "status" in result

    def test_audio_part_with_different_extensions(self):
        """Test _audio_part with different audio file extensions."""
        client = SonotheiaClient(api_key="test-key")

        # Test with different extensions
        test_cases = [
            ("test.wav", "audio/wav"),
            ("test.mp3", "audio/mpeg"),
            ("test.opus", "audio/opus"),
            ("test.flac", "audio/flac"),
            ("test.unknown", "application/octet-stream"),  # Fallback
        ]

        for filename, expected_mime in test_cases:
            with patch("builtins.open", mock_open(read_data=b"data")) as mock_file:
                file_obj = mock_file.return_value.__enter__.return_value
                result_filename, result_file, result_mime = client._audio_part(filename, file_obj)
                assert result_filename == filename
                assert result_mime == expected_mime
