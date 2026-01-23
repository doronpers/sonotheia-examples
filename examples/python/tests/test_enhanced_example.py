"""Tests for enhanced_example.py - enhanced CLI example."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest

# Skip tests if enhanced_example not available
try:
    from enhanced_example import main
except ImportError:
    pytestmark = pytest.mark.skip("enhanced_example not available")


class TestEnhancedExample:
    """Tests for enhanced_example.py main function."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock enhanced client."""
        client = MagicMock()
        client.__enter__ = Mock(return_value=client)
        client.__exit__ = Mock(return_value=False)
        client.detect_deepfake.return_value = {
            "score": 0.3,
            "label": "likely_real",
            "latency_ms": 450,
        }
        client.verify_mfa.return_value = {
            "verified": True,
            "confidence": 0.85,
        }
        client.submit_sar.return_value = {
            "status": "submitted",
            "case_id": "case-123",
        }
        return client

    @patch("enhanced_example.SonotheiaClientEnhanced")
    def test_main_basic_deepfake(self, mock_client_class, mock_client, test_audio):
        """Test basic deepfake detection."""
        mock_client_class.return_value = mock_client
        mock_client.__enter__.return_value = mock_client

        with patch("enhanced_example.sys.argv", ["enhanced_example.py", test_audio]):
            with patch("enhanced_example.sys.exit") as mock_exit:
                try:
                    main()
                except SystemExit:
                    pass
                # Exit should be called
                assert mock_exit.called

        mock_client.detect_deepfake.assert_called_once()

    @patch("enhanced_example.SonotheiaClientEnhanced")
    def test_main_with_mfa(self, mock_client_class, mock_client, test_audio):
        """Test with MFA verification."""
        mock_client_class.return_value = mock_client
        mock_client.__enter__.return_value = mock_client

        with patch(
            "enhanced_example.sys.argv",
            ["enhanced_example.py", test_audio, "--enrollment-id", "enroll-123"],
        ):
            with patch("enhanced_example.sys.exit") as mock_exit:
                try:
                    main()
                except SystemExit:
                    pass
                assert mock_exit.called

        mock_client.verify_mfa.assert_called_once()

    @patch("enhanced_example.SonotheiaClientEnhanced")
    def test_main_with_sar(self, mock_client_class, mock_client, test_audio):
        """Test with SAR submission."""
        mock_client_class.return_value = mock_client
        mock_client.__enter__.return_value = mock_client

        with patch(
            "enhanced_example.sys.argv",
            [
                "enhanced_example.py",
                test_audio,
                "--session-id",
                "session-123",
                "--decision",
                "deny",
            ],
        ):
            with patch("enhanced_example.sys.exit") as mock_exit:
                try:
                    main()
                except SystemExit:
                    pass
                assert mock_exit.called

        mock_client.submit_sar.assert_called_once()

    @patch("enhanced_example.SonotheiaClientEnhanced")
    def test_main_with_retry_config(self, mock_client_class, mock_client, test_audio):
        """Test with custom retry configuration."""
        mock_client_class.return_value = mock_client
        mock_client.__enter__.return_value = mock_client

        with patch(
            "enhanced_example.sys.argv", ["enhanced_example.py", test_audio, "--max-retries", "5"]
        ):
            with patch("enhanced_example.sys.exit") as mock_exit:
                try:
                    main()
                except SystemExit:
                    pass
                assert mock_exit.called

        # Verify client was initialized with max_retries=5
        mock_client_class.assert_called_once()
        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["max_retries"] == 5

    @patch("enhanced_example.SonotheiaClientEnhanced")
    def test_main_with_rate_limit(self, mock_client_class, mock_client, test_audio):
        """Test with rate limiting."""
        mock_client_class.return_value = mock_client
        mock_client.__enter__.return_value = mock_client

        with patch(
            "enhanced_example.sys.argv", ["enhanced_example.py", test_audio, "--rate-limit", "2.0"]
        ):
            with patch("enhanced_example.sys.exit") as mock_exit:
                try:
                    main()
                except SystemExit:
                    pass
                assert mock_exit.called

        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["rate_limit_rps"] == 2.0

    @patch("enhanced_example.SonotheiaClientEnhanced")
    def test_main_with_circuit_breaker_disabled(self, mock_client_class, mock_client, test_audio):
        """Test with circuit breaker disabled."""
        mock_client_class.return_value = mock_client
        mock_client.__enter__.return_value = mock_client

        with patch(
            "enhanced_example.sys.argv",
            ["enhanced_example.py", test_audio, "--disable-circuit-breaker"],
        ):
            with patch("enhanced_example.sys.exit") as mock_exit:
                try:
                    main()
                except SystemExit:
                    pass
                assert mock_exit.called

        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["enable_circuit_breaker"] is False

    @patch("enhanced_example.SonotheiaClientEnhanced")
    def test_main_error_handling(self, mock_client_class, mock_client, test_audio):
        """Test error handling."""
        mock_client_class.return_value = mock_client
        mock_client.__enter__.return_value = mock_client

        import requests

        mock_client.detect_deepfake.side_effect = requests.HTTPError("API Error")

        with patch("enhanced_example.sys.argv", ["enhanced_example.py", test_audio]):
            with patch("enhanced_example.sys.exit") as mock_exit:
                try:
                    main()
                except SystemExit:
                    pass
                # Should exit with non-zero on error
                assert mock_exit.called
                # Check that exit was called with error code
                assert any(call[0][0] != 0 for call in mock_exit.call_args_list if call[0])

    @patch("enhanced_example.SonotheiaClientEnhanced")
    def test_main_missing_audio_file(self, mock_client_class):
        """Test handling of missing audio file."""
        with patch("enhanced_example.sys.argv", ["enhanced_example.py", "nonexistent.wav"]):
            with patch("enhanced_example.sys.exit") as mock_exit:
                try:
                    main()
                except SystemExit:
                    pass
                # Should exit with non-zero on file not found
                assert mock_exit.called
