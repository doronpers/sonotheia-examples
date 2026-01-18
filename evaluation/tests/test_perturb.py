"""Tests for perturbations."""

import numpy as np
import pytest

from audio_trust_harness.perturb import (
    CodecStubPerturbation,
    NoisePerturbation,
    NonePerturbation,
    PitchShiftPerturbation,
    TimeStretchPerturbation,
    get_perturbation,
)


def test_none_perturbation():
    """Test that NonePerturbation returns identical audio."""
    audio = np.random.randn(1000)
    perturb = NonePerturbation(seed=1337)

    result = perturb.apply(audio, sample_rate=16000)

    assert np.array_equal(result, audio)
    assert result is not audio  # Should be a copy


def test_noise_perturbation_deterministic():
    """Test that NoisePerturbation is deterministic with same seed."""
    audio = np.random.randn(1000)

    perturb1 = NoisePerturbation(snr_db=20.0, seed=1337)
    perturb2 = NoisePerturbation(snr_db=20.0, seed=1337)

    result1 = perturb1.apply(audio, sample_rate=16000)
    result2 = perturb2.apply(audio, sample_rate=16000)

    assert np.allclose(result1, result2)


def test_noise_perturbation_different_seeds():
    """Test that NoisePerturbation produces different results with different seeds."""
    audio = np.random.randn(1000)

    perturb1 = NoisePerturbation(snr_db=20.0, seed=1337)
    perturb2 = NoisePerturbation(snr_db=20.0, seed=42)

    result1 = perturb1.apply(audio, sample_rate=16000)
    result2 = perturb2.apply(audio, sample_rate=16000)

    assert not np.allclose(result1, result2)


def test_noise_perturbation_adds_noise():
    """Test that NoisePerturbation actually adds noise."""
    audio = np.zeros(1000)  # Silent audio

    perturb = NoisePerturbation(snr_db=20.0, seed=1337)
    result = perturb.apply(audio, sample_rate=16000)

    # Result should not be silent
    assert np.std(result) > 0
    assert not np.allclose(result, audio)


def test_noise_perturbation_params():
    """Test that NoisePerturbation returns correct params."""
    perturb = NoisePerturbation(snr_db=15.0, seed=42)
    params = perturb.get_params()

    assert params["snr_db"] == 15.0
    assert params["seed"] == 42


def test_codec_stub_perturbation_deterministic():
    """Test that CodecStubPerturbation is deterministic."""
    audio = np.random.randn(1000)

    perturb1 = CodecStubPerturbation(cutoff_hz=3400, bits=8, seed=1337)
    perturb2 = CodecStubPerturbation(cutoff_hz=3400, bits=8, seed=1337)

    result1 = perturb1.apply(audio, sample_rate=16000)
    result2 = perturb2.apply(audio, sample_rate=16000)

    assert np.allclose(result1, result2)


def test_codec_stub_perturbation_lowpass():
    """Test that CodecStubPerturbation filters high frequencies."""
    # Create audio with high frequency content
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))

    # Mix of low (440Hz) and high (6000Hz) frequencies
    audio = np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 6000 * t)

    perturb = CodecStubPerturbation(cutoff_hz=3400, bits=16, seed=1337)
    result = perturb.apply(audio, sample_rate=sr)

    # Result should have less high frequency content
    # Check by computing FFT
    fft_orig = np.abs(np.fft.rfft(audio))
    fft_filtered = np.abs(np.fft.rfft(result))

    # High frequency component should be attenuated
    high_freq_idx = int(6000 * len(fft_orig) / (sr / 2))
    assert fft_filtered[high_freq_idx] < fft_orig[high_freq_idx]


def test_codec_stub_perturbation_quantization():
    """Test that CodecStubPerturbation quantizes audio."""
    audio = np.random.randn(1000) * 0.1  # Small amplitude variations

    perturb = CodecStubPerturbation(cutoff_hz=8000, bits=4, seed=1337)
    result = perturb.apply(audio, sample_rate=16000)

    # Quantized audio should have fewer unique values
    unique_orig = len(np.unique(np.round(audio, 6)))
    unique_quant = len(np.unique(np.round(result, 6)))

    assert unique_quant < unique_orig


def test_codec_stub_perturbation_params():
    """Test that CodecStubPerturbation returns correct params."""
    perturb = CodecStubPerturbation(cutoff_hz=4000, bits=12, seed=99)
    params = perturb.get_params()

    assert params["cutoff_hz"] == 4000
    assert params["bits"] == 12
    assert params["seed"] == 99


def test_get_perturbation_none():
    """Test factory function for none perturbation."""
    perturb = get_perturbation("none", seed=1337)
    assert isinstance(perturb, NonePerturbation)


def test_get_perturbation_noise():
    """Test factory function for noise perturbation."""
    perturb = get_perturbation("noise", seed=1337, snr_db=15.0)
    assert isinstance(perturb, NoisePerturbation)


def test_get_perturbation_codec_stub():
    """Test factory function for codec_stub perturbation."""
    perturb = get_perturbation("codec_stub", seed=1337, cutoff_hz=4000, bits=10)
    assert isinstance(perturb, CodecStubPerturbation)


def test_get_perturbation_unknown():
    """Test that factory function raises error for unknown perturbation."""
    with pytest.raises(ValueError, match="Unknown perturbation"):
        get_perturbation("unknown_perturb", seed=1337)


def test_pitch_shift_perturbation_deterministic():
    """Test that PitchShiftPerturbation is deterministic."""
    audio = np.random.randn(1000)

    perturb1 = PitchShiftPerturbation(semitones=2.0, seed=1337)
    perturb2 = PitchShiftPerturbation(semitones=2.0, seed=1337)

    result1 = perturb1.apply(audio, sample_rate=16000)
    result2 = perturb2.apply(audio, sample_rate=16000)

    assert np.allclose(result1, result2)


def test_pitch_shift_perturbation_changes_audio():
    """Test that PitchShiftPerturbation modifies audio."""
    audio = np.random.randn(1000)

    perturb = PitchShiftPerturbation(semitones=2.0, seed=1337)
    result = perturb.apply(audio, sample_rate=16000)

    # Result should be different from original
    assert not np.allclose(result, audio)
    # Result should have same length (padded/trimmed)
    assert len(result) == len(audio)


def test_pitch_shift_perturbation_params():
    """Test that PitchShiftPerturbation returns correct params."""
    perturb = PitchShiftPerturbation(semitones=3.5, seed=42)
    params = perturb.get_params()

    assert params["semitones"] == 3.5
    assert params["seed"] == 42


def test_time_stretch_perturbation_deterministic():
    """Test that TimeStretchPerturbation is deterministic."""
    audio = np.random.randn(1000)

    perturb1 = TimeStretchPerturbation(rate=1.2, seed=1337)
    perturb2 = TimeStretchPerturbation(rate=1.2, seed=1337)

    result1 = perturb1.apply(audio, sample_rate=16000)
    result2 = perturb2.apply(audio, sample_rate=16000)

    assert np.allclose(result1, result2)


def test_time_stretch_perturbation_changes_audio():
    """Test that TimeStretchPerturbation modifies audio."""
    audio = np.random.randn(1000)

    perturb = TimeStretchPerturbation(rate=1.2, seed=1337)
    result = perturb.apply(audio, sample_rate=16000)

    # Result should be different from original
    assert not np.allclose(result, audio)
    # Result should have same length (padded/trimmed)
    assert len(result) == len(audio)


def test_time_stretch_perturbation_params():
    """Test that TimeStretchPerturbation returns correct params."""
    perturb = TimeStretchPerturbation(rate=0.8, seed=99)
    params = perturb.get_params()

    assert params["rate"] == 0.8
    assert params["seed"] == 99


def test_get_perturbation_pitch_shift():
    """Test factory function for pitch_shift perturbation."""
    perturb = get_perturbation("pitch_shift", seed=1337, semitones=3.0)
    assert isinstance(perturb, PitchShiftPerturbation)


def test_get_perturbation_time_stretch():
    """Test factory function for time_stretch perturbation."""
    perturb = get_perturbation("time_stretch", seed=1337, rate=1.5)
    assert isinstance(perturb, TimeStretchPerturbation)


def test_pitch_shift_perturbation_validates_semitones():
    """Test that PitchShiftPerturbation validates semitones range."""
    # Should accept valid range
    PitchShiftPerturbation(semitones=-24, seed=1337)
    PitchShiftPerturbation(semitones=24, seed=1337)
    PitchShiftPerturbation(semitones=0, seed=1337)

    # Should reject out of range
    with pytest.raises(ValueError, match="semitones must be in range"):
        PitchShiftPerturbation(semitones=-25, seed=1337)

    with pytest.raises(ValueError, match="semitones must be in range"):
        PitchShiftPerturbation(semitones=25, seed=1337)


def test_time_stretch_perturbation_validates_rate():
    """Test that TimeStretchPerturbation validates rate range."""
    # Should accept valid range
    TimeStretchPerturbation(rate=0.25, seed=1337)
    TimeStretchPerturbation(rate=4.0, seed=1337)
    TimeStretchPerturbation(rate=1.0, seed=1337)

    # Should reject out of range
    with pytest.raises(ValueError, match="rate must be in range"):
        TimeStretchPerturbation(rate=0.24, seed=1337)

    with pytest.raises(ValueError, match="rate must be in range"):
        TimeStretchPerturbation(rate=4.1, seed=1337)

    with pytest.raises(ValueError, match="rate must be in range"):
        TimeStretchPerturbation(rate=0, seed=1337)
