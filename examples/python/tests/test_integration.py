"""
Integration tests using mock API server.

These tests start a mock API server and run integration tests against it,
validating the full request/response cycle without requiring real API credentials.

Run tests:
    pytest test_integration.py -v

Run with real API (requires credentials):
    SONOTHEIA_API_KEY=your_key pytest test_integration.py -v --real-api
"""

import os
import subprocess
import tempfile
import time

import pytest
import requests

# Test constants
MOCK_API_KEY = "mock_api_key_12345"
MOCK_API_PORT = 8001
MOCK_API_URL = f"http://localhost:{MOCK_API_PORT}"


def create_test_audio_file(duration_seconds: float = 5.0) -> str:
    """Create a test WAV file using ffmpeg."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_file.close()

    # Generate silent audio
    command = [
        "ffmpeg",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=16000:cl=mono",
        "-t",
        str(duration_seconds),
        "-y",
        temp_file.name,
    ]

    try:
        subprocess.run(command, capture_output=True, check=True)
        return temp_file.name
    except subprocess.CalledProcessError:
        pytest.skip("ffmpeg not available - cannot create test audio files")
    except FileNotFoundError:
        pytest.skip("ffmpeg not available - cannot create test audio files")


@pytest.fixture(scope="module")
def mock_server():
    """Start mock API server for tests."""
    # Check if we should use real API
    if os.environ.get("REAL_API"):
        api_key = os.environ.get("SONOTHEIA_API_KEY")
        api_url = os.environ.get("SONOTHEIA_API_URL", "https://api.sonotheia.com")

        if not api_key:
            pytest.skip("SONOTHEIA_API_KEY not set for real API tests")

        yield {"api_key": api_key, "api_url": api_url, "process": None}
        return

    # Start mock server
    import sys

    # Start server in subprocess
    process = subprocess.Popen(
        [sys.executable, "mock_api_server.py", "--port", str(MOCK_API_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    max_retries = 30
    for _i in range(max_retries):
        try:
            response = requests.get(f"{MOCK_API_URL}/health", timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            time.sleep(0.5)
    else:
        process.kill()
        pytest.fail("Mock server failed to start")

    # Configure mock server to disable error simulation for deterministic tests
    try:
        requests.post(
            f"{MOCK_API_URL}/mock/config",
            json={"always_succeed": True},
            timeout=5,
        )
    except requests.exceptions.RequestException:
        pass  # Best effort, continue if config update fails

    yield {"api_key": MOCK_API_KEY, "api_url": MOCK_API_URL, "process": process}

    # Cleanup
    process.terminate()
    process.wait(timeout=5)


@pytest.fixture
def test_audio():
    """Create a test audio file."""
    audio_path = create_test_audio_file(duration_seconds=5.0)
    yield audio_path
    os.unlink(audio_path)


@pytest.fixture
def client(mock_server):
    """Create a client configured for the test server."""
    from client import SonotheiaClient

    return SonotheiaClient(
        api_key=mock_server["api_key"], api_url=mock_server["api_url"]
    )


class TestDeepfakeDetection:
    """Integration tests for deepfake detection."""

    def test_basic_detection(self, client, test_audio):
        """Test basic deepfake detection."""
        result = client.detect_deepfake(test_audio)

        assert "score" in result
        assert "label" in result
        assert "session_id" in result
        assert 0.0 <= result["score"] <= 1.0
        assert result["label"] in ["likely_real", "likely_synthetic", "uncertain"]

    def test_detection_with_metadata(self, client, test_audio):
        """Test deepfake detection with metadata."""
        metadata = {
            "session_id": "test-session-123",
            "channel": "ivr",
            "user_id": "user-456",
        }

        result = client.detect_deepfake(test_audio, metadata=metadata)

        assert "score" in result
        assert "session_id" in result

    def test_detection_with_synthetic_filename(self, client):
        """Test that synthetic filename affects score (mock server behavior)."""
        # Create audio with 'synthetic' in filename
        audio_path = create_test_audio_file(duration_seconds=5.0)
        synthetic_path = audio_path.replace(".wav", "_synthetic.wav")
        os.rename(audio_path, synthetic_path)

        try:
            result = client.detect_deepfake(synthetic_path)

            # Mock server returns higher scores for files with 'synthetic' in name
            assert result["score"] > 0.6
            assert result["label"] in ["likely_synthetic", "uncertain"]
        finally:
            os.unlink(synthetic_path)

    def test_detection_with_real_filename(self, client):
        """Test that real filename affects score (mock server behavior)."""
        # Create audio with 'real' in filename
        audio_path = create_test_audio_file(duration_seconds=5.0)
        real_path = audio_path.replace(".wav", "_real.wav")
        os.rename(audio_path, real_path)

        try:
            result = client.detect_deepfake(real_path)

            # Mock server returns lower scores for files with 'real' in name
            assert result["score"] < 0.4
            assert result["label"] in ["likely_real", "uncertain"]
        finally:
            os.unlink(real_path)


class TestMFAVerification:
    """Integration tests for MFA verification."""

    def test_basic_verification(self, client, test_audio):
        """Test basic MFA verification."""
        enrollment_id = "test-enrollment-123"

        result = client.verify_mfa(test_audio, enrollment_id)

        assert "verified" in result
        assert "enrollment_id" in result
        assert "confidence" in result
        assert result["enrollment_id"] == enrollment_id
        assert isinstance(result["verified"], bool)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_verification_with_context(self, client, test_audio):
        """Test MFA verification with context."""
        enrollment_id = "test-enrollment-456"
        context = {
            "session_id": "mfa-session-789",
            "channel": "mobile_app",
            "ip_address": "192.168.1.1",
        }

        result = client.verify_mfa(test_audio, enrollment_id, context=context)

        assert "verified" in result
        assert "enrollment_id" in result
        assert result["enrollment_id"] == enrollment_id

    def test_verification_with_match_filename(self, client):
        """Test that match filename affects verification (mock server behavior)."""
        audio_path = create_test_audio_file(duration_seconds=5.0)
        match_path = audio_path.replace(".wav", "_match.wav")
        os.rename(audio_path, match_path)

        try:
            result = client.verify_mfa(match_path, "test-enrollment")

            # Mock server returns high confidence for files with 'match' in name
            assert result["verified"] is True
            assert result["confidence"] > 0.8
        finally:
            os.unlink(match_path)

    def test_verification_with_mismatch_filename(self, client):
        """Test that mismatch filename affects verification (mock server behavior)."""
        audio_path = create_test_audio_file(duration_seconds=5.0)
        mismatch_path = audio_path.replace(".wav", "_mismatch.wav")
        os.rename(audio_path, mismatch_path)

        try:
            result = client.verify_mfa(mismatch_path, "test-enrollment")

            # Mock server returns low confidence for files with 'mismatch' in name
            assert result["verified"] is False
            assert result["confidence"] < 0.5
        finally:
            os.unlink(mismatch_path)


class TestSARSubmission:
    """Integration tests for SAR submission."""

    def test_basic_submission(self, client):
        """Test basic SAR submission."""
        result = client.submit_sar(
            session_id="test-session-123",
            decision="review",
            reason="Suspicious activity detected",
        )

        assert "status" in result
        assert "case_id" in result
        assert "session_id" in result
        assert result["status"] == "submitted"
        assert result["session_id"] == "test-session-123"

    def test_submission_with_metadata(self, client):
        """Test SAR submission with metadata."""
        metadata = {
            "user_id": "user-789",
            "risk_score": 0.85,
            "reviewer": "automated-system",
        }

        result = client.submit_sar(
            session_id="test-session-456",
            decision="deny",
            reason="High risk detected",
            metadata=metadata,
        )

        assert "status" in result
        assert "case_id" in result
        assert result["status"] == "submitted"

    @pytest.mark.parametrize("decision", ["allow", "deny", "review"])
    def test_all_decision_types(self, client, decision):
        """Test all valid decision types."""
        result = client.submit_sar(
            session_id=f"test-session-{decision}",
            decision=decision,
            reason=f"Test {decision} decision",
        )

        assert result["status"] == "submitted"
        assert "case_id" in result


class TestWorkflowIntegration:
    """Integration tests for complete workflows."""

    def test_full_workflow(self, client, test_audio):
        """Test complete workflow: deepfake -> MFA -> SAR."""
        # Step 1: Deepfake detection
        deepfake_result = client.detect_deepfake(
            test_audio, metadata={"session_id": "workflow-test-123"}
        )

        assert "session_id" in deepfake_result
        session_id = deepfake_result["session_id"]

        # Step 2: MFA verification
        mfa_result = client.verify_mfa(
            test_audio,
            enrollment_id="test-enrollment",
            context={"session_id": session_id},
        )

        assert "verified" in mfa_result

        # Step 3: SAR submission based on results
        if deepfake_result["score"] > 0.7 or not mfa_result["verified"]:
            sar_result = client.submit_sar(
                session_id=session_id,
                decision="review",
                reason="Suspicious signals detected",
                metadata={
                    "deepfake_score": deepfake_result["score"],
                    "mfa_verified": mfa_result["verified"],
                },
            )

            assert sar_result["status"] == "submitted"
            assert sar_result["session_id"] == session_id


class TestErrorHandling:
    """Integration tests for error handling."""

    def test_invalid_api_key(self, mock_server, test_audio):
        """Test handling of invalid API key."""
        from client import SonotheiaClient

        # Skip if using real API
        if mock_server["process"] is None:
            pytest.skip("Cannot test with real API")

        client = SonotheiaClient(api_key="invalid_key", api_url=mock_server["api_url"])

        with pytest.raises(requests.HTTPError) as exc_info:
            client.detect_deepfake(test_audio)

        assert exc_info.value.response.status_code == 401

    def test_missing_audio_file(self, client):
        """Test handling of missing audio file."""
        with pytest.raises(FileNotFoundError):
            client.detect_deepfake("nonexistent_file.wav")

    def test_empty_audio_file(self, client):
        """Test handling of empty audio file."""
        # Create empty file
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_file.close()

        try:
            with pytest.raises(requests.HTTPError) as exc_info:
                client.detect_deepfake(temp_file.name)

            assert exc_info.value.response.status_code == 400
        finally:
            os.unlink(temp_file.name)


class TestMockServerFeatures:
    """Tests for mock server specific features."""

    def test_health_check(self, mock_server):
        """Test mock server health endpoint."""
        if mock_server["process"] is None:
            pytest.skip("Not using mock server")

        response = requests.get(f"{mock_server['api_url']}/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_mock_stats(self, mock_server, client, test_audio):
        """Test mock server statistics."""
        if mock_server["process"] is None:
            pytest.skip("Not using mock server")

        # Make some API calls
        client.detect_deepfake(test_audio)
        client.verify_mfa(test_audio, "test-enrollment")

        # Get stats
        response = requests.get(f"{mock_server['api_url']}/mock/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_sessions" in data
        assert data["total_sessions"] >= 1

    def test_mock_reset(self, mock_server):
        """Test mock server reset functionality."""
        if mock_server["process"] is None:
            pytest.skip("Not using mock server")

        response = requests.post(f"{mock_server['api_url']}/mock/reset")

        assert response.status_code == 200
        assert response.json()["status"] == "reset"
