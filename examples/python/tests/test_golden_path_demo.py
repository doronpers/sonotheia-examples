"""Unit tests for Golden Path Demo."""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from golden_path_demo import get_audio_info, make_routing_decision, run_golden_path


class TestGetAudioInfo:
    """Test cases for get_audio_info function."""

    def test_get_audio_info_with_soundfile(self, tmp_path: Path):
        """Test get_audio_info using soundfile."""
        # Create a dummy audio file
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"dummy audio data")

        # Mock soundfile module
        mock_sf = MagicMock()
        mock_info = Mock()
        mock_info.duration = 5.5
        mock_info.samplerate = 16000
        mock_sf.info.return_value = mock_info

        with patch("golden_path_demo.sf", mock_sf, create=True):
            result = get_audio_info(audio_file)

            assert result["audio_seconds"] == 5.5
            assert result["samplerate_hz"] == 16000

    def test_get_audio_info_with_ffprobe(self, tmp_path: Path):
        """Test get_audio_info using ffprobe fallback."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"dummy audio data")

        with patch("golden_path_demo.sf", side_effect=ImportError("No module")):
            with patch("golden_path_demo.subprocess.run") as mock_run:
                mock_result = Mock()
                mock_result.stdout = json.dumps(
                    {
                        "format": {"duration": "7.2"},
                        "streams": [{"sample_rate": "44100"}],
                    }
                )
                mock_result.returncode = 0
                mock_run.return_value = mock_result

                result = get_audio_info(audio_file)

                assert result["audio_seconds"] == 7.2
                assert result["samplerate_hz"] == 44100

    def test_get_audio_info_fallback_to_defaults(self, tmp_path: Path):
        """Test get_audio_info falls back to defaults on error."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"dummy audio data")

        with patch("golden_path_demo.sf", side_effect=ImportError("No module")):
            with patch("golden_path_demo.subprocess.run", side_effect=FileNotFoundError()):
                result = get_audio_info(audio_file)

                assert result["audio_seconds"] == 0.0
                assert result["samplerate_hz"] == 16000


class TestMakeRoutingDecision:
    """Test cases for make_routing_decision function."""

    def test_routing_allow_low_risk(self):
        """Test routing decision for low risk scenario."""
        deepfake_result = {
            "score": 0.2,
            "label": "likely_real",
            "recommended_action": "allow",
        }

        decision = make_routing_decision(deepfake_result)

        assert decision["route"] == "ALLOW"
        assert len(decision["reasons"]) == 0

    def test_routing_escalate_high_deepfake_score(self):
        """Test routing decision for high deepfake score."""
        deepfake_result = {
            "score": 0.85,
            "label": "likely_synthetic",
            "recommended_action": "defer_to_review",
        }

        decision = make_routing_decision(deepfake_result)

        assert decision["route"] == "ESCALATE_TO_HUMAN"
        assert "deepfake_defer" in decision["reasons"]

    def test_routing_step_up_elevated_risk(self):
        """Test routing decision for elevated risk."""
        deepfake_result = {
            "score": 0.65,
            "label": "uncertain",
            "recommended_action": "review",
        }

        decision = make_routing_decision(deepfake_result)

        assert decision["route"] == "REQUIRE_STEP_UP"
        assert "elevated_risk" in decision["reasons"]

    def test_routing_with_mfa_failure(self):
        """Test routing decision when MFA verification fails."""
        deepfake_result = {
            "score": 0.3,
            "label": "likely_real",
            "recommended_action": "allow",
        }
        mfa_result = {
            "verified": False,
            "enrollment_id": "enroll-123",
            "confidence": 0.4,
        }

        decision = make_routing_decision(deepfake_result, mfa_result)

        assert decision["route"] == "REQUIRE_STEP_UP"
        assert "mfa_verification_failed" in decision["reasons"]

    def test_routing_with_low_mfa_confidence(self):
        """Test routing decision with low MFA confidence."""
        deepfake_result = {
            "score": 0.3,
            "label": "likely_real",
            "recommended_action": "allow",
        }
        mfa_result = {
            "verified": True,
            "enrollment_id": "enroll-123",
            "confidence": 0.65,  # Below 0.7 threshold
        }

        decision = make_routing_decision(deepfake_result, mfa_result)

        assert decision["route"] == "REQUIRE_STEP_UP"
        assert "low_mfa_confidence" in decision["reasons"]

    def test_routing_sar_policy_auto(self):
        """Test SAR submission policy auto."""
        deepfake_result = {
            "score": 0.85,  # High score triggers SAR
            "label": "likely_synthetic",
            "recommended_action": "defer_to_review",
        }

        decision = make_routing_decision(deepfake_result, sar_policy="auto")

        assert decision["should_submit_sar"] is True
        assert "sar_required" in decision["reasons"]

    def test_routing_sar_policy_never(self):
        """Test SAR submission policy never."""
        deepfake_result = {
            "score": 0.85,
            "label": "likely_synthetic",
            "recommended_action": "defer_to_review",
        }

        decision = make_routing_decision(deepfake_result, sar_policy="never")

        assert decision["should_submit_sar"] is False

    def test_routing_sar_policy_always(self):
        """Test SAR submission policy always."""
        deepfake_result = {
            "score": 0.2,
            "label": "likely_real",
            "recommended_action": "allow",
        }

        decision = make_routing_decision(deepfake_result, sar_policy="always")

        assert decision["should_submit_sar"] is True
        assert "sar_required" in decision["reasons"]


class TestRunGoldenPath:
    """Test cases for run_golden_path function."""

    @pytest.fixture
    def mock_audio_file(self, tmp_path: Path) -> Path:
        """Create a mock audio file for testing."""
        audio_file = tmp_path / "test_audio.wav"
        audio_file.write_bytes(b"fake audio data")
        return audio_file

    @pytest.fixture
    def mock_client(self):
        """Create a mock SonotheiaClient."""
        client = Mock()
        client.detect_deepfake.return_value = {
            "score": 0.3,
            "label": "likely_real",
            "latency_ms": 450,
            "session_id": "test-session",
        }
        client.verify_mfa.return_value = {
            "verified": True,
            "enrollment_id": "enroll-123",
            "confidence": 0.85,
            "latency_ms": 320,
        }
        client.submit_sar.return_value = {
            "status": "submitted",
            "case_id": "sar-001234",
            "session_id": "test-session",
        }
        return client

    @patch("golden_path_demo.SonotheiaClient")
    @patch("golden_path_demo.get_audio_info")
    def test_run_golden_path_basic(
        self, mock_get_audio_info, mock_client_class, mock_audio_file: Path, mock_client
    ):
        """Test basic golden path execution."""
        mock_get_audio_info.return_value = {"audio_seconds": 5.0, "samplerate_hz": 16000}
        mock_client_class.return_value = mock_client

        result = run_golden_path(
            audio_path=mock_audio_file,
            mock_mode=True,
        )

        # Verify structure
        assert "session_id" in result
        assert "timestamp" in result
        assert "inputs" in result
        assert "results" in result
        assert "decision" in result
        assert "diagnostics" in result

        # Verify results
        assert "deepfake" in result["results"]
        assert result["results"]["mfa"] is None  # No enrollment ID
        assert result["results"]["sar"] is None  # No SAR by default

        # Verify decision
        assert result["decision"]["route"] == "ALLOW"

        # Verify client was called
        mock_client.detect_deepfake.assert_called_once()

    @patch("golden_path_demo.SonotheiaClient")
    @patch("golden_path_demo.get_audio_info")
    def test_run_golden_path_with_mfa(
        self, mock_get_audio_info, mock_client_class, mock_audio_file: Path, mock_client
    ):
        """Test golden path with MFA verification."""
        mock_get_audio_info.return_value = {"audio_seconds": 5.0, "samplerate_hz": 16000}
        mock_client_class.return_value = mock_client

        result = run_golden_path(
            audio_path=mock_audio_file,
            enrollment_id="enroll-123",
            mock_mode=True,
        )

        # Verify MFA was called
        mock_client.verify_mfa.assert_called_once()
        assert result["results"]["mfa"] is not None
        assert result["results"]["mfa"]["verified"] is True

    @patch("golden_path_demo.SonotheiaClient")
    @patch("golden_path_demo.get_audio_info")
    def test_run_golden_path_with_sar(
        self, mock_get_audio_info, mock_client_class, mock_audio_file: Path, mock_client
    ):
        """Test golden path with SAR submission."""
        mock_get_audio_info.return_value = {"audio_seconds": 5.0, "samplerate_hz": 16000}
        # Set high deepfake score to trigger SAR
        mock_client.detect_deepfake.return_value = {
            "score": 0.85,
            "label": "likely_synthetic",
            "recommended_action": "defer_to_review",
            "latency_ms": 450,
        }
        mock_client_class.return_value = mock_client

        result = run_golden_path(
            audio_path=mock_audio_file,
            session_id="test-session",
            sar_policy="auto",
            mock_mode=True,
        )

        # Verify SAR was called
        mock_client.submit_sar.assert_called_once()
        assert result["results"]["sar"] is not None
        assert result["results"]["sar"]["status"] == "submitted"

    @patch("golden_path_demo.SonotheiaClient")
    @patch("golden_path_demo.get_audio_info")
    def test_run_golden_path_mfa_failure_handling(
        self, mock_get_audio_info, mock_client_class, mock_audio_file: Path, mock_client
    ):
        """Test golden path handles MFA failure gracefully."""
        mock_get_audio_info.return_value = {"audio_seconds": 5.0, "samplerate_hz": 16000}
        mock_client.verify_mfa.side_effect = requests.HTTPError("MFA failed")
        mock_client_class.return_value = mock_client

        result = run_golden_path(
            audio_path=mock_audio_file,
            enrollment_id="enroll-123",
            mock_mode=True,
        )

        # Should continue despite MFA failure
        assert result["results"]["mfa"] is None
        assert "deepfake" in result["results"]  # Deepfake should still work

    @patch("golden_path_demo.SonotheiaClient")
    @patch("golden_path_demo.get_audio_info")
    def test_run_golden_path_sar_failure_handling(
        self, mock_get_audio_info, mock_client_class, mock_audio_file: Path, mock_client
    ):
        """Test golden path handles SAR failure gracefully."""
        mock_get_audio_info.return_value = {"audio_seconds": 5.0, "samplerate_hz": 16000}
        mock_client.detect_deepfake.return_value = {
            "score": 0.85,
            "label": "likely_synthetic",
            "recommended_action": "defer_to_review",
            "latency_ms": 450,
        }
        mock_client.submit_sar.side_effect = requests.HTTPError("SAR failed")
        mock_client_class.return_value = mock_client

        result = run_golden_path(
            audio_path=mock_audio_file,
            session_id="test-session",
            sar_policy="auto",
            mock_mode=True,
        )

        # Should continue despite SAR failure
        assert result["results"]["sar"] is None
        assert "deepfake" in result["results"]  # Deepfake should still work

    @patch("golden_path_demo.SonotheiaClient")
    @patch("golden_path_demo.get_audio_info")
    def test_run_golden_path_deepfake_error_propagates(
        self, mock_get_audio_info, mock_client_class, mock_audio_file: Path, mock_client
    ):
        """Test that deepfake detection errors are not swallowed."""
        mock_get_audio_info.return_value = {"audio_seconds": 5.0, "samplerate_hz": 16000}
        mock_client.detect_deepfake.side_effect = requests.HTTPError("API error")
        mock_client_class.return_value = mock_client

        with pytest.raises(requests.HTTPError):
            run_golden_path(
                audio_path=mock_audio_file,
                mock_mode=True,
            )

    @patch("golden_path_demo.SonotheiaClient")
    @patch("golden_path_demo.get_audio_info")
    def test_run_golden_path_output_structure(
        self, mock_get_audio_info, mock_client_class, mock_audio_file: Path, mock_client
    ):
        """Test that output matches the standardized contract."""
        mock_get_audio_info.return_value = {"audio_seconds": 7.2, "samplerate_hz": 16000}
        mock_client_class.return_value = mock_client

        result = run_golden_path(
            audio_path=mock_audio_file,
            enrollment_id="enroll-123",
            session_id="test-session",
            mock_mode=True,
        )

        # Verify top-level structure
        assert "session_id" in result
        assert "timestamp" in result
        assert "inputs" in result
        assert "results" in result
        assert "decision" in result
        assert "diagnostics" in result

        # Verify inputs structure
        assert "audio_filename" in result["inputs"]
        assert "audio_seconds" in result["inputs"]
        assert "samplerate_hz" in result["inputs"]

        # Verify results structure
        assert "deepfake" in result["results"]
        assert "mfa" in result["results"]
        assert "sar" in result["results"]

        # Verify decision structure
        assert "route" in result["decision"]
        assert "reasons" in result["decision"]
        assert "explainability" in result["decision"]

        # Verify JSON serializability
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed == result

    @patch("golden_path_demo.SonotheiaClient")
    @patch("golden_path_demo.get_audio_info")
    def test_run_golden_path_numpy_type_conversion(
        self, mock_get_audio_info, mock_client_class, mock_audio_file: Path, mock_client
    ):
        """Test that numpy types are converted to native Python types."""
        try:
            import numpy as np
        except ImportError:
            pytest.skip("numpy not available")

        mock_get_audio_info.return_value = {"audio_seconds": 5.0, "samplerate_hz": 16000}
        # Return numpy types in response
        mock_client.detect_deepfake.return_value = {
            "score": np.float64(0.3),
            "label": "likely_real",
            "latency_ms": np.int64(450),
            "session_id": "test-session",
        }
        mock_client_class.return_value = mock_client

        result = run_golden_path(
            audio_path=mock_audio_file,
            mock_mode=True,
        )

        # Verify types are native Python
        assert isinstance(result["results"]["deepfake"]["score"], float)
        assert isinstance(result["results"]["deepfake"]["latency_ms"], int)

        # Verify JSON serialization works
        json_str = json.dumps(result)
        assert "0.3" in json_str
        assert "450" in json_str
