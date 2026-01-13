"""
Tests for indicators.
"""

import numpy as np

from audio_trust_harness.indicators import (
    CrestFactorIndicator,
    RMSEnergyIndicator,
    SpectralCentroidIndicator,
    SpectralFlatnessIndicator,
    SpectralRolloffIndicator,
    ZeroCrossingRateIndicator,
)


def test_spectral_centroid_indicator():
    """Test SpectralCentroidIndicator returns expected keys and numeric types."""
    # Generate sine wave
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))
    audio = np.sin(2 * np.pi * 440 * t)

    indicator = SpectralCentroidIndicator()
    result = indicator.compute(audio, sr)

    # Check keys
    assert "spectral_centroid_mean" in result
    assert "spectral_centroid_std" in result

    # Check types
    assert isinstance(result["spectral_centroid_mean"], float)
    assert isinstance(result["spectral_centroid_std"], float)

    # Check reasonable values
    assert result["spectral_centroid_mean"] > 0
    assert result["spectral_centroid_std"] >= 0


def test_spectral_centroid_higher_frequency():
    """Test that higher frequency audio has higher spectral centroid."""
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))

    # Low frequency (440Hz)
    audio_low = np.sin(2 * np.pi * 440 * t)

    # High frequency (2000Hz)
    audio_high = np.sin(2 * np.pi * 2000 * t)

    indicator = SpectralCentroidIndicator()
    result_low = indicator.compute(audio_low, sr)
    result_high = indicator.compute(audio_high, sr)

    assert result_high["spectral_centroid_mean"] > result_low["spectral_centroid_mean"]


def test_spectral_flatness_indicator():
    """Test SpectralFlatnessIndicator returns expected keys and numeric types."""
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))
    audio = np.sin(2 * np.pi * 440 * t)

    indicator = SpectralFlatnessIndicator()
    result = indicator.compute(audio, sr)

    # Check keys
    assert "spectral_flatness_mean" in result
    assert "spectral_flatness_std" in result

    # Check types
    assert isinstance(result["spectral_flatness_mean"], float)
    assert isinstance(result["spectral_flatness_std"], float)

    # Check reasonable values (flatness is 0-1)
    assert 0 <= result["spectral_flatness_mean"] <= 1
    assert result["spectral_flatness_std"] >= 0


def test_spectral_flatness_tone_vs_noise():
    """Test that pure tone has lower flatness than noise."""
    sr = 16000
    duration = 1.0

    # Pure tone (low flatness)
    t = np.linspace(0, duration, int(sr * duration))
    audio_tone = np.sin(2 * np.pi * 440 * t)

    # White noise (high flatness)
    np.random.seed(42)
    audio_noise = np.random.randn(int(sr * duration)) * 0.5

    indicator = SpectralFlatnessIndicator()
    result_tone = indicator.compute(audio_tone, sr)
    result_noise = indicator.compute(audio_noise, sr)

    assert (
        result_tone["spectral_flatness_mean"] < result_noise["spectral_flatness_mean"]
    )


def test_rms_energy_indicator():
    """Test RMSEnergyIndicator returns expected keys and numeric types."""
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))
    audio = np.sin(2 * np.pi * 440 * t) * 0.5

    indicator = RMSEnergyIndicator()
    result = indicator.compute(audio, sr)

    # Check keys
    assert "rms_energy" in result

    # Check type
    assert isinstance(result["rms_energy"], float)

    # Check reasonable value
    assert result["rms_energy"] > 0


def test_rms_energy_louder_audio():
    """Test that louder audio has higher RMS energy."""
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))

    # Quiet audio
    audio_quiet = np.sin(2 * np.pi * 440 * t) * 0.1

    # Loud audio
    audio_loud = np.sin(2 * np.pi * 440 * t) * 0.8

    indicator = RMSEnergyIndicator()
    result_quiet = indicator.compute(audio_quiet, sr)
    result_loud = indicator.compute(audio_loud, sr)

    assert result_loud["rms_energy"] > result_quiet["rms_energy"]


def test_crest_factor_indicator():
    """Test CrestFactorIndicator returns expected keys and numeric types."""
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))
    audio = np.sin(2 * np.pi * 440 * t)

    indicator = CrestFactorIndicator()
    result = indicator.compute(audio, sr)

    # Check keys
    assert "crest_factor" in result

    # Check type
    assert isinstance(result["crest_factor"], float)

    # Check reasonable value
    assert result["crest_factor"] > 0


def test_crest_factor_sine_vs_square():
    """Test that different waveforms have different crest factors."""
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))

    # Sine wave (moderate crest factor)
    audio_sine = np.sin(2 * np.pi * 440 * t)

    # Square wave (lower crest factor, more uniform)
    audio_square = np.sign(np.sin(2 * np.pi * 440 * t))

    indicator = CrestFactorIndicator()
    result_sine = indicator.compute(audio_sine, sr)
    result_square = indicator.compute(audio_square, sr)

    # Sine wave should have higher crest factor than square wave
    assert result_sine["crest_factor"] > result_square["crest_factor"]


def test_indicators_on_silent_audio():
    """Test that indicators handle silent audio gracefully."""
    sr = 16000
    audio = np.zeros(sr)  # 1 second of silence

    indicators = [
        SpectralCentroidIndicator(),
        SpectralFlatnessIndicator(),
        SpectralRolloffIndicator(),
        RMSEnergyIndicator(),
        CrestFactorIndicator(),
        ZeroCrossingRateIndicator(),
    ]

    for indicator in indicators:
        result = indicator.compute(audio, sr)
        # Should return valid numeric values (even if zero)
        for value in result.values():
            assert isinstance(value, (int, float))
            assert not np.isnan(value)
            assert not np.isinf(value)


def test_zero_crossing_rate_indicator():
    """Test ZeroCrossingRateIndicator returns expected keys and numeric types."""
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))
    audio = np.sin(2 * np.pi * 440 * t)

    indicator = ZeroCrossingRateIndicator()
    result = indicator.compute(audio, sr)

    # Check keys
    assert "zero_crossing_rate" in result

    # Check type
    assert isinstance(result["zero_crossing_rate"], float)

    # Check reasonable value (should be positive)
    assert result["zero_crossing_rate"] >= 0


def test_zero_crossing_rate_frequency():
    """Test that higher frequency has higher zero-crossing rate."""
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))

    # Low frequency (440Hz)
    audio_low = np.sin(2 * np.pi * 440 * t)

    # High frequency (2000Hz)
    audio_high = np.sin(2 * np.pi * 2000 * t)

    indicator = ZeroCrossingRateIndicator()
    result_low = indicator.compute(audio_low, sr)
    result_high = indicator.compute(audio_high, sr)

    assert result_high["zero_crossing_rate"] > result_low["zero_crossing_rate"]


def test_spectral_rolloff_indicator():
    """Test SpectralRolloffIndicator returns expected keys and numeric types."""
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))
    audio = np.sin(2 * np.pi * 440 * t)

    indicator = SpectralRolloffIndicator()
    result = indicator.compute(audio, sr)

    # Check keys
    assert "spectral_rolloff_mean" in result
    assert "spectral_rolloff_std" in result

    # Check types
    assert isinstance(result["spectral_rolloff_mean"], float)
    assert isinstance(result["spectral_rolloff_std"], float)

    # Check reasonable values (should be between 0 and Nyquist frequency)
    assert 0 <= result["spectral_rolloff_mean"] <= sr / 2
    assert result["spectral_rolloff_std"] >= 0


def test_spectral_rolloff_higher_frequency():
    """Test that higher frequency audio has higher spectral rolloff."""
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))

    # Low frequency (440Hz)
    audio_low = np.sin(2 * np.pi * 440 * t)

    # High frequency (2000Hz)
    audio_high = np.sin(2 * np.pi * 2000 * t)

    indicator = SpectralRolloffIndicator()
    result_low = indicator.compute(audio_low, sr)
    result_high = indicator.compute(audio_high, sr)

    assert result_high["spectral_rolloff_mean"] > result_low["spectral_rolloff_mean"]
