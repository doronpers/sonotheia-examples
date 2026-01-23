"""Tests for load_test.py - load testing utilities."""

from __future__ import annotations

import pytest

# Skip tests if load_test not available
try:
    from load_test import TestAudioGenerator
except ImportError:
    pytestmark = pytest.mark.skip("load_test not available")


class TestTestAudioGenerator:
    """Tests for TestAudioGenerator class."""

    def test_create_test_audio_default_duration(self):
        """Test creating test audio with default duration."""
        audio_data = TestAudioGenerator.create_test_audio()

        assert isinstance(audio_data, bytes)
        assert len(audio_data) > 0
        # WAV header should be present
        assert audio_data.startswith(b"RIFF")
        assert b"WAVE" in audio_data

    def test_create_test_audio_custom_duration(self):
        """Test creating test audio with custom duration."""
        audio_data = TestAudioGenerator.create_test_audio(duration_seconds=10.0)

        assert isinstance(audio_data, bytes)
        assert len(audio_data) > 0
        # Longer duration should produce larger file
        assert len(audio_data) > TestAudioGenerator.create_test_audio(duration_seconds=1.0)

    def test_create_test_audio_structure(self):
        """Test test audio file structure."""
        audio_data = TestAudioGenerator.create_test_audio(duration_seconds=5.0)

        # Verify WAV structure
        assert audio_data[:4] == b"RIFF"
        assert b"WAVE" in audio_data
        assert b"fmt " in audio_data
        assert b"data" in audio_data

    def test_create_test_audio_different_durations(self):
        """Test creating audio files with different durations."""
        durations = [1.0, 5.0, 10.0, 30.0]

        for duration in durations:
            audio_data = TestAudioGenerator.create_test_audio(duration_seconds=duration)
            assert isinstance(audio_data, bytes)
            assert len(audio_data) > 0

        # Verify longer durations produce larger files
        short_audio = TestAudioGenerator.create_test_audio(duration_seconds=1.0)
        long_audio = TestAudioGenerator.create_test_audio(duration_seconds=30.0)
        assert len(long_audio) > len(short_audio)
