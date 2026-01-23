"""
Shared pytest fixtures for Sonotheia Python examples tests.

This module provides common fixtures used across multiple test files to reduce
duplication and ensure consistent test setup.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time

import pytest
import requests

# Test constants
MOCK_API_KEY = "mock_api_key_12345"
MOCK_API_PORT = 8914
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
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("ffmpeg not available - cannot create test audio files")
        return ""  # Never reached, but satisfies type checker


@pytest.fixture(scope="module")
def mock_server():
    """
    Start mock API server for integration tests.

    This fixture starts a mock API server in a subprocess and waits for it to be ready.
    The server is automatically stopped after all tests in the module complete.
    """
    # Check if we should use real API
    if os.environ.get("REAL_API"):
        api_key = os.environ.get("SONOTHEIA_API_KEY")
        api_url = os.environ.get("SONOTHEIA_API_URL", "https://api.sonotheia.com")

        if not api_key:
            pytest.skip("SONOTHEIA_API_KEY not set for real API tests")

        yield {"api_key": api_key, "api_url": api_url, "process": None}
        return

    # Check if Flask is available (required for mock server)
    try:
        import flask  # noqa: F401
    except ImportError:
        pytest.skip("Flask not available - mock server requires Flask")

    # Determine path to mock_api_server.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    mock_server_path = os.path.join(current_dir, "..", "mock_api_server.py")

    if not os.path.exists(mock_server_path):
        pytest.skip(f"Mock server script not found: {mock_server_path}")

    # Start server in subprocess
    process = subprocess.Popen(
        [sys.executable, mock_server_path, "--port", str(MOCK_API_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(mock_server_path),
    )

    # Wait for server to start
    max_retries = 30
    started = False
    for _i in range(max_retries):
        try:
            response = requests.get(f"{MOCK_API_URL}/health", timeout=1)
            if response.status_code == 200:
                started = True
                break
        except requests.exceptions.RequestException:
            time.sleep(0.5)

    if not started:
        # Get error output before killing
        try:
            stdout, stderr = process.communicate(timeout=1)
            error_msg = (
                f"Mock server failed to start. "
                f"stdout: {stdout.decode() if stdout else 'empty'}, "
                f"stderr: {stderr.decode() if stderr else 'empty'}"
            )
        except subprocess.TimeoutExpired:
            error_msg = "Mock server failed to start (timeout getting error output)"
        process.kill()
        pytest.fail(f"Mock server failed to start: {error_msg}")

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
    try:
        process.terminate()
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)


@pytest.fixture
def test_audio():
    """
    Create a test audio file for testing.

    The file is automatically cleaned up after the test completes.
    """
    audio_path = create_test_audio_file(duration_seconds=5.0)
    yield audio_path
    try:
        os.unlink(audio_path)
    except OSError:
        pass  # File may have already been deleted


@pytest.fixture
def client(mock_server):
    """
    Create a SonotheiaClient instance configured for testing.

    Uses the mock_server fixture to get the correct API URL and key.
    """
    from client import SonotheiaClient

    return SonotheiaClient(
        api_key=mock_server["api_key"],
        api_url=mock_server["api_url"],
    )
