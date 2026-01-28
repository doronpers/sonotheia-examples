"""
Pytest configuration for examples/python tests.

Handles path setup and common fixtures for all tests.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add parent directory (examples/python) to path for imports
sys.path.insert(0, str(Path(__file__).parent))


# Configure asyncio to use a single event loop for tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_api_key():
    """Provide a test API key."""
    return "test_key_12345_sonotheia"


@pytest.fixture
def test_audio_data():
    """Provide mock audio data for testing."""
    import numpy as np

    # Generate a simple sine wave as test audio
    sample_rate = 16000
    duration = 1  # 1 second
    frequency = 440  # A4 note

    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio = np.sin(2 * np.pi * frequency * t) * 0.3
    return audio.astype(np.float32)


@pytest.fixture
def mock_response():
    """Provide a mock API response."""
    return {
        "is_genuine": True,
        "confidence": 0.95,
        "analysis": {
            "spectral_features": {"stable": True},
            "temporal_features": {"consistent": True},
            "voice_characteristics": {"natural": True},
        },
        "reason": "Voice authentication successful",
        "details": {
            "processing_time_ms": 45.2,
            "audio_quality": "high",
            "sample_rate": 16000,
        },
    }


@pytest.fixture
def mock_http_client(mock_response):
    """Provide a mock HTTP client for testing API calls."""
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.get.return_value = {"status": "healthy"}
    return mock_client


@pytest.fixture
def temp_audio_file(tmp_path, test_audio_data):
    """Create a temporary audio file for testing."""
    try:
        import soundfile as sf
    except ImportError:
        pytest.skip("soundfile not installed")

    audio_file = tmp_path / "test_audio.wav"
    sf.write(str(audio_file), test_audio_data, 16000)
    return str(audio_file)
