"""Tests for audio_analysis_example.py - audio analysis with DSP features."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock, patch

import pytest
import requests

# Skip tests if audio_analysis_example not available
try:
    from audio_analysis_example import AudioAnalysisClient, interpret_results, main
except ImportError:
    pytestmark = pytest.mark.skip("audio_analysis_example not available")


class TestAudioAnalysisClient:
    """Tests for AudioAnalysisClient class."""

    @pytest.fixture
    def client(self):
        """Create an AudioAnalysisClient instance."""
        return AudioAnalysisClient(api_key="test-key", api_url="https://api.test.com")

    def test_init(self, client):
        """Test client initialization."""
        assert client.api_key == "test-key"
        assert client.api_url == "https://api.test.com"
        assert client.tenant_id == "demo"

    def test_init_with_tenant(self):
        """Test client initialization with custom tenant."""
        client = AudioAnalysisClient(api_key="test-key", tenant_id="custom-tenant")
        assert client.tenant_id == "custom-tenant"

    def test_headers(self, client):
        """Test header generation."""
        headers = client._headers()
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["X-Tenant-ID"] == "demo"
        assert headers["Accept"] == "application/json"

    @patch("audio_analysis_example.requests.post")
    def test_analyze_audio_success(self, mock_post, client, test_audio):
        """Test successful audio analysis."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "score": 0.3,
            "label": "likely_real",
            "confidence": 0.85,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = client.analyze_audio(test_audio, extract_features=True)

        assert result["score"] == 0.3
        assert result["label"] == "likely_real"
        mock_post.assert_called_once()

    @patch("audio_analysis_example.requests.post")
    def test_analyze_audio_missing_file(self, mock_post, client):
        """Test analysis with missing file."""
        with pytest.raises(FileNotFoundError):
            client.analyze_audio("nonexistent.wav")

    @patch("audio_analysis_example.requests.post")
    def test_analyze_audio_http_error(self, mock_post, client, test_audio):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("API Error")
        mock_post.return_value = mock_response

        with pytest.raises(requests.HTTPError):
            client.analyze_audio(test_audio)

    @patch("audio_analysis_example.requests.post")
    def test_extract_features_only(self, mock_post, client, test_audio):
        """Test feature extraction only."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "features": {"spectral": {}, "temporal": {}},
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result: dict[str, Any] = client.extract_features_only(test_audio)

        assert "features" in result
        mock_post.assert_called_once()


class TestInterpretResults:
    """Tests for interpret_results function."""

    def test_interpret_low_score(self):
        """Test interpretation of low score (likely real)."""
        result = {"score": 0.2, "confidence": 0.9}
        action = interpret_results(result)
        assert "allow" in action.lower() or "proceed" in action.lower()

    def test_interpret_high_score(self):
        """Test interpretation of high score (likely synthetic)."""
        result = {"score": 0.9, "confidence": 0.95}
        action = interpret_results(result)
        assert "deny" in action.lower() or "block" in action.lower() or "review" in action.lower()

    def test_interpret_medium_score(self):
        """Test interpretation of medium score (uncertain)."""
        result = {"score": 0.5, "confidence": 0.6}
        action = interpret_results(result)
        assert "review" in action.lower() or "verify" in action.lower()

    def test_interpret_missing_fields(self):
        """Test interpretation with missing fields."""
        result: dict[str, Any] = {}
        action = interpret_results(result)
        assert isinstance(action, str)
        assert len(action) > 0


class TestMainFunction:
    """Tests for main function."""

    @patch("audio_analysis_example.AudioAnalysisClient")
    @patch("audio_analysis_example.os.path.exists")
    def test_main_success(self, mock_exists, mock_client_class, test_audio, tmp_path):
        """Test successful main execution."""
        mock_client = Mock()
        mock_client.analyze_audio.return_value = {
            "score": 0.3,
            "label": "likely_real",
        }
        mock_client_class.return_value = mock_client
        mock_exists.return_value = True

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        with patch(
            "audio_analysis_example.sys.argv", ["audio_analysis_example.py", str(audio_file)]
        ):
            with patch("audio_analysis_example.sys.exit") as mock_exit:
                try:
                    main()
                except SystemExit:
                    pass
                assert mock_exit.called

        mock_client.analyze_audio.assert_called_once()

    @patch("audio_analysis_example.os.path.exists")
    def test_main_missing_file(self, mock_exists):
        """Test main with missing file."""
        mock_exists.return_value = False

        with patch(
            "audio_analysis_example.sys.argv", ["audio_analysis_example.py", "nonexistent.wav"]
        ):
            with patch("audio_analysis_example.sys.exit") as mock_exit:
                try:
                    main()
                except SystemExit:
                    pass
                # Should exit with error
                assert mock_exit.called
