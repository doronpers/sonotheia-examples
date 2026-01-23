"""
Tests for main.py CLI module.

This module tests the command-line interface functionality.
"""

from __future__ import annotations

import json
import sys
from unittest.mock import Mock, patch

import pytest

# Import main function
import main


class TestHandleAPIErrors:
    """Tests for handle_api_errors context manager."""

    def test_handle_api_errors_success(self):
        """Test that context manager doesn't interfere with successful operations."""
        with main.handle_api_errors("Test operation"):
            # Should not raise
            pass

    def test_handle_api_errors_http_error(self):
        """Test that HTTP errors are handled correctly."""
        import requests

        with pytest.raises(SystemExit):
            with main.handle_api_errors("Test operation"):
                error = requests.HTTPError("Bad Request")
                error.response = Mock()
                error.response.text = "Error message"
                raise error

    def test_handle_api_errors_generic_exception(self):
        """Test that generic exceptions are handled correctly."""
        with pytest.raises(SystemExit):
            with main.handle_api_errors("Test operation"):
                raise ValueError("Test error")


class TestMainFunction:
    """Tests for main() function."""

    @patch("main.SonotheiaClient")
    def test_main_with_valid_audio_file(self, mock_client_class, tmp_path, monkeypatch):
        """Test main with valid audio file."""
        # Create test audio file
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data" * 100)

        # Mock client
        mock_client = Mock()
        mock_client.detect_deepfake.return_value = {
            "score": 0.5,
            "label": "likely_real",
            "latency_ms": 100,
        }
        mock_client_class.return_value = mock_client

        # Set API key
        monkeypatch.setenv("SONOTHEIA_API_KEY", "test-key")

        # Mock sys.argv
        with patch.object(sys, "argv", ["main.py", str(audio_file)]):
            with patch("builtins.print") as mock_print:
                main.main()
                # Should print JSON output
                assert mock_print.called

    @patch("main.SonotheiaClient")
    def test_main_with_invalid_extension(self, mock_client_class, tmp_path, monkeypatch):
        """Test main with invalid file extension."""
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_bytes(b"data")

        monkeypatch.setenv("SONOTHEIA_API_KEY", "test-key")

        with patch.object(sys, "argv", ["main.py", str(invalid_file)]):
            with pytest.raises(SystemExit):
                main.main()

    @patch("main.SonotheiaClient")
    def test_main_with_missing_file(self, mock_client_class, monkeypatch):
        """Test main with missing file."""
        monkeypatch.setenv("SONOTHEIA_API_KEY", "test-key")

        with patch.object(sys, "argv", ["main.py", "/nonexistent/file.wav"]):
            with pytest.raises(SystemExit):
                main.main()

    @patch("main.SonotheiaClient")
    def test_main_with_enrollment_id(self, mock_client_class, tmp_path, monkeypatch):
        """Test main with enrollment ID."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data" * 100)

        mock_client = Mock()
        mock_client.detect_deepfake.return_value = {
            "score": 0.5,
            "label": "likely_real",
            "latency_ms": 100,
        }
        mock_client.verify_mfa.return_value = {
            "verified": True,
            "enrollment_id": "enroll-123",
            "confidence": 0.9,
        }
        mock_client_class.return_value = mock_client

        monkeypatch.setenv("SONOTHEIA_API_KEY", "test-key")

        with patch.object(
            sys, "argv", ["main.py", str(audio_file), "--enrollment-id", "enroll-123"]
        ):
            with patch("builtins.print"):
                main.main()
                # Should call verify_mfa
                mock_client.verify_mfa.assert_called_once()

    @patch("main.SonotheiaClient")
    def test_main_with_session_id(self, mock_client_class, tmp_path, monkeypatch):
        """Test main with session ID."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data" * 100)

        mock_client = Mock()
        mock_client.detect_deepfake.return_value = {
            "score": 0.5,
            "label": "likely_real",
            "latency_ms": 100,
        }
        mock_client.submit_sar.return_value = {
            "status": "submitted",
            "case_id": "case-123",
            "session_id": "session-123",
        }
        mock_client_class.return_value = mock_client

        monkeypatch.setenv("SONOTHEIA_API_KEY", "test-key")

        with patch.object(sys, "argv", ["main.py", str(audio_file), "--session-id", "session-123"]):
            with patch("builtins.print"):
                main.main()
                # Should call submit_sar
                mock_client.submit_sar.assert_called_once()

    @patch("main.SonotheiaClient")
    def test_main_output_to_file(self, mock_client_class, tmp_path, monkeypatch):
        """Test main with output file."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data" * 100)
        output_file = tmp_path / "output.json"

        mock_client = Mock()
        mock_client.detect_deepfake.return_value = {
            "score": 0.5,
            "label": "likely_real",
            "latency_ms": 100,
        }
        mock_client_class.return_value = mock_client

        monkeypatch.setenv("SONOTHEIA_API_KEY", "test-key")

        with patch.object(sys, "argv", ["main.py", str(audio_file), "--output", str(output_file)]):
            with patch("builtins.print"):
                main.main()
                # Should create output file
                assert output_file.exists()
                # Should contain JSON
                data = json.loads(output_file.read_text())
                assert "deepfake" in data

    @patch("main.SonotheiaClient")
    def test_main_pretty_print(self, mock_client_class, tmp_path, monkeypatch):
        """Test main with pretty print option."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data" * 100)

        mock_client = Mock()
        mock_client.detect_deepfake.return_value = {
            "score": 0.5,
            "label": "likely_real",
            "latency_ms": 100,
        }
        mock_client_class.return_value = mock_client

        monkeypatch.setenv("SONOTHEIA_API_KEY", "test-key")

        with patch.object(sys, "argv", ["main.py", str(audio_file), "--pretty"]):
            with patch("builtins.print") as mock_print:
                main.main()
                # Should be called with formatted output
                assert mock_print.called

    def test_main_error_handling_missing_api_key(self, tmp_path, monkeypatch):
        """Test main error handling when API key is missing."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data" * 100)

        monkeypatch.delenv("SONOTHEIA_API_KEY", raising=False)

        with patch.object(sys, "argv", ["main.py", str(audio_file)]):
            with pytest.raises(SystemExit):
                main.main()
