"""Tests for streaming_example.py - streaming audio processor."""

from __future__ import annotations

import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest

# Skip tests if streaming_example not available
try:
    from streaming_example import process_streaming, split_audio_file
except ImportError:
    pytestmark = pytest.mark.skip("streaming_example not available")


class TestSplitAudioFile:
    """Tests for split_audio_file function."""

    @pytest.fixture
    def test_audio_path(self, test_audio):
        """Return path to test audio file."""
        return test_audio

    @patch("subprocess.run")
    def test_split_audio_file_success(self, mock_run, test_audio_path):
        """Test successful audio file splitting."""
        # Mock ffprobe to return duration
        mock_probe = Mock()
        mock_probe.stdout = "10.5\n"
        mock_probe.returncode = 0
        mock_probe.check_returncode = Mock()

        # Mock ffmpeg split command
        mock_split = Mock()
        mock_split.returncode = 0
        mock_split.check_returncode = Mock()

        # Configure mock_run to return different values for probe vs split
        call_count = [0]

        def run_side_effect(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("args", [])
            call_count[0] += 1
            if "ffprobe" in str(cmd):
                return mock_probe
            return mock_split

        mock_run.side_effect = run_side_effect

        chunks = list(split_audio_file(test_audio_path, chunk_duration_seconds=5))
        assert len(chunks) > 0
        assert all(isinstance(chunk[0], int) for chunk in chunks)
        assert all(isinstance(chunk[1], str) for chunk in chunks)

    @patch("subprocess.run")
    def test_split_audio_file_probe_failure(self, mock_run, test_audio_path):
        """Test handling of ffprobe failure."""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "ffprobe")

        with pytest.raises(subprocess.CalledProcessError):
            list(split_audio_file(test_audio_path, chunk_duration_seconds=5))

    @patch("subprocess.run")
    def test_split_audio_file_custom_output_dir(self, mock_run, test_audio_path):
        """Test splitting with custom output directory."""
        mock_probe = Mock()
        mock_probe.stdout = "10.5\n"
        mock_probe.returncode = 0

        mock_split = Mock()
        mock_split.returncode = 0

        def run_side_effect(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("args", [])
            if "ffprobe" in cmd:
                return mock_probe
            return mock_split

        mock_run.side_effect = run_side_effect

        with tempfile.TemporaryDirectory() as tmpdir:
            chunks = list(
                split_audio_file(test_audio_path, chunk_duration_seconds=5, output_dir=tmpdir)
            )
            assert len(chunks) > 0
            # Verify chunks are in the specified directory
            for _, chunk_path in chunks:
                assert chunk_path.startswith(tmpdir)

    def test_split_audio_file_missing_ffmpeg(self, test_audio_path):
        """Test error when ffmpeg is not available."""
        with patch("builtins.__import__", side_effect=ImportError("No module named 'subprocess'")):
            with pytest.raises(ImportError, match="ffmpeg"):
                list(split_audio_file(test_audio_path, chunk_duration_seconds=5))


class TestProcessStreaming:
    """Tests for process_streaming function."""

    @patch("streaming_example.split_audio_file")
    @patch("streaming_example.SonotheiaClientEnhanced")
    def test_process_streaming_success(self, mock_client_class, mock_split, test_audio):
        """Test successful streaming processing."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.detect_deepfake.return_value = {
            "score": 0.3,
            "label": "likely_real",
            "latency_ms": 450,
        }
        mock_client_class.return_value = mock_client

        # Mock split to return chunks
        mock_split.return_value = [
            (0, test_audio),
            (1, test_audio),
        ]

        results = process_streaming(test_audio, chunk_duration=5)

        assert "session_id" in results
        assert "chunks" in results
        assert "summary" in results
        assert len(results["chunks"]) == 2

    @patch("streaming_example.split_audio_file")
    @patch("streaming_example.SonotheiaClientEnhanced")
    def test_process_streaming_with_mfa(self, mock_client_class, mock_split, test_audio):
        """Test streaming processing with MFA verification."""
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.detect_deepfake.return_value = {"score": 0.3, "label": "likely_real"}
        mock_client.verify_mfa.return_value = {"verified": True, "confidence": 0.85}
        mock_client_class.return_value = mock_client

        mock_split.return_value = [(0, test_audio)]

        results = process_streaming(
            test_audio,
            chunk_duration=5,
            enrollment_id="test-enroll",
        )

        assert len(results["chunks"]) > 0
        assert "mfa" in results["chunks"][0]

    @patch("streaming_example.split_audio_file")
    @patch("streaming_example.SonotheiaClientEnhanced")
    def test_process_streaming_error_handling(self, mock_client_class, mock_split, test_audio):
        """Test error handling during streaming."""
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client_class.return_value = mock_client

        mock_split.return_value = [(0, test_audio)]

        # Make client raise an error
        import requests

        mock_client.detect_deepfake.side_effect = requests.HTTPError("API Error")

        results = process_streaming(test_audio, chunk_duration=5)

        assert len(results["chunks"]) > 0
        assert "error" in results["chunks"][0]

    @patch("streaming_example.split_audio_file")
    @patch("streaming_example.SonotheiaClientEnhanced")
    def test_process_streaming_empty_chunks(self, mock_client_class, mock_split, test_audio):
        """Test handling of empty chunk list."""
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client_class.return_value = mock_client

        mock_split.return_value = []

        results = process_streaming(test_audio, chunk_duration=5)

        assert results["summary"]["total_chunks"] == 0
        assert len(results["chunks"]) == 0
