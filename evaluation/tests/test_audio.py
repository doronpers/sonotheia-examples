"""Tests for audio module."""

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from audio_trust_harness.audio import (
    LIBROSA_AVAILABLE,
    ResampleBackend,
    detect_clipping,
    load_audio,
    slice_audio,
)


@pytest.fixture
def temp_wav_file(tmp_path):
    """Create a temporary WAV file for testing."""
    # Generate 2 seconds of sine wave at 440Hz
    duration = 2.0
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)

    wav_path = tmp_path / "test.wav"
    sf.write(wav_path, audio, sample_rate)

    return wav_path, audio, sample_rate, duration


def test_load_audio_file_not_found():
    """Test that loading non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_audio(Path("nonexistent.wav"))


def test_load_audio_success(temp_wav_file):
    """Test successful audio loading."""
    wav_path, expected_audio, expected_sr, duration = temp_wav_file

    audio, sr = load_audio(wav_path, target_sr=16000)

    assert sr == 16000
    assert len(audio) == len(expected_audio)
    assert np.allclose(audio, expected_audio, atol=0.01)


def test_slice_audio_non_overlapping(temp_wav_file):
    """Test slicing audio with non-overlapping slices."""
    wav_path, audio, sr, duration = temp_wav_file

    slices = slice_audio(audio, sr, slice_seconds=1.0, hop_seconds=1.0)

    # Should get 2 slices from 2 seconds of audio
    assert len(slices) == 2

    # Check first slice
    assert slices[0].slice_index == 0
    assert slices[0].start_time == 0.0
    assert slices[0].duration == 1.0
    assert slices[0].sample_rate == sr
    assert len(slices[0].data) == sr

    # Check second slice
    assert slices[1].slice_index == 1
    assert slices[1].start_time == 1.0
    assert slices[1].duration == 1.0


def test_slice_audio_with_max_slices(temp_wav_file):
    """Test slicing with max_slices limit."""
    wav_path, audio, sr, duration = temp_wav_file

    slices = slice_audio(audio, sr, slice_seconds=0.5, hop_seconds=0.5, max_slices=2)

    assert len(slices) == 2


def test_slice_audio_overlapping(temp_wav_file):
    """Test slicing audio with overlapping slices."""
    wav_path, audio, sr, duration = temp_wav_file

    slices = slice_audio(audio, sr, slice_seconds=1.0, hop_seconds=0.5)

    # Should get 3 slices: 0-1s, 0.5-1.5s, 1-2s
    assert len(slices) == 3
    assert slices[1].start_time == 0.5


def test_slice_audio_invalid_params(temp_wav_file):
    """Validate slice_audio rejects non-positive parameters."""
    wav_path, audio, sr, duration = temp_wav_file

    with pytest.raises(ValueError, match="slice_seconds must be positive"):
        slice_audio(audio, sr, slice_seconds=0.0, hop_seconds=1.0)

    with pytest.raises(ValueError, match="hop_seconds must be positive"):
        slice_audio(audio, sr, slice_seconds=1.0, hop_seconds=0.0)

    with pytest.raises(ValueError, match="max_slices must be positive"):
        slice_audio(audio, sr, slice_seconds=0.1, hop_seconds=0.1, max_slices=0)


def test_detect_clipping_no_clipping():
    """Test clipping detection on normal audio."""
    audio = np.random.randn(1000) * 0.3
    audio = np.clip(audio, -0.9, 0.9)  # Ensure no clipping
    assert not detect_clipping(audio, threshold=0.95)


def test_detect_clipping_with_clipping():
    """Test clipping detection on clipped audio."""
    audio = np.random.randn(1000)
    audio[100] = 1.0  # Clipped sample
    assert detect_clipping(audio, threshold=0.95)


def test_audio_slice_properties(temp_wav_file):
    """Test AudioSlice properties."""
    wav_path, audio, sr, duration = temp_wav_file

    slices = slice_audio(audio, sr, slice_seconds=1.0, hop_seconds=1.0)
    slice_obj = slices[0]

    assert slice_obj.num_samples == len(slice_obj.data)
    assert slice_obj.num_samples == sr  # 1 second at 16kHz


class TestResampleBackend:
    """Tests for resampling backend options."""

    def test_resample_backend_enum(self):
        """Test ResampleBackend enum values."""
        assert ResampleBackend.SCIPY.value == "scipy"
        assert ResampleBackend.LIBROSA.value == "librosa"

    def test_load_audio_with_scipy_backend(self, tmp_path):
        """Test loading audio with scipy backend."""
        # Create test file at different sample rate
        duration = 0.5
        original_sr = 44100
        t = np.linspace(0, duration, int(original_sr * duration))
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)

        wav_path = tmp_path / "test_44k.wav"
        sf.write(wav_path, audio.astype(np.float32), original_sr)

        # Load with scipy backend (default)
        data, sr = load_audio(wav_path, target_sr=16000, resample_backend="scipy")

        assert sr == 16000
        expected_samples = int(duration * 16000)
        assert abs(len(data) - expected_samples) <= 1

    def test_load_audio_with_scipy_backend_enum(self, tmp_path):
        """Test loading audio with scipy backend using enum."""
        duration = 0.5
        original_sr = 44100
        t = np.linspace(0, duration, int(original_sr * duration))
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)

        wav_path = tmp_path / "test_44k.wav"
        sf.write(wav_path, audio.astype(np.float32), original_sr)

        data, sr = load_audio(wav_path, target_sr=16000, resample_backend=ResampleBackend.SCIPY)

        assert sr == 16000

    @pytest.mark.skipif(not LIBROSA_AVAILABLE, reason="librosa not installed")
    def test_load_audio_with_librosa_backend(self, tmp_path):
        """Test loading audio with librosa backend."""
        duration = 0.5
        original_sr = 44100
        t = np.linspace(0, duration, int(original_sr * duration))
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)

        wav_path = tmp_path / "test_44k.wav"
        sf.write(wav_path, audio.astype(np.float32), original_sr)

        data, sr = load_audio(wav_path, target_sr=16000, resample_backend="librosa")

        assert sr == 16000
        expected_samples = int(duration * 16000)
        assert abs(len(data) - expected_samples) <= 1

    def test_load_audio_invalid_backend(self, tmp_path):
        """Test that invalid backend raises ValueError."""
        duration = 0.5
        sample_rate = 16000
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)

        wav_path = tmp_path / "test.wav"
        sf.write(wav_path, audio.astype(np.float32), sample_rate)

        with pytest.raises(ValueError, match="Invalid resample backend"):
            load_audio(wav_path, target_sr=16000, resample_backend="invalid")

    def test_librosa_unavailable_error(self, tmp_path, monkeypatch):
        """Test error when librosa backend requested but not available."""
        duration = 0.5
        sample_rate = 16000
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)

        wav_path = tmp_path / "test.wav"
        sf.write(wav_path, audio.astype(np.float32), sample_rate)

        # Mock librosa as unavailable
        import audio_trust_harness.audio as audio_module

        monkeypatch.setattr(audio_module, "LIBROSA_AVAILABLE", False)

        with pytest.raises(ValueError, match="librosa is not installed"):
            load_audio(wav_path, target_sr=16000, resample_backend="librosa")
