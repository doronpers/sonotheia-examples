"""Tests for cross-slice consistency checks."""

import numpy as np

from audio_trust_harness.calibrate import ConsistencyChecker


def test_consistency_checker_consistent_slices():
    """Test that similar slices are marked as consistent."""
    # Create slices with similar indicator values
    slice_indicators = [
        {"rms_energy": 0.1, "spectral_centroid_mean": 1500.0},
        {"rms_energy": 0.11, "spectral_centroid_mean": 1520.0},
        {"rms_energy": 0.09, "spectral_centroid_mean": 1480.0},
    ]

    checker = ConsistencyChecker(threshold=0.5)
    result = checker.evaluate(slice_indicators)

    assert result.is_consistent
    assert result.inconsistency_score < 0.5
    assert len(result.inconsistent_indicators) == 0


def test_consistency_checker_inconsistent_slices():
    """Test that dramatically different slices are marked as inconsistent."""
    # Create slices with dramatically different indicator values
    slice_indicators = [
        {"rms_energy": 0.1, "spectral_centroid_mean": 1500.0},
        {"rms_energy": 0.5, "spectral_centroid_mean": 5000.0},  # Large jump
        {"rms_energy": 0.12, "spectral_centroid_mean": 1600.0},
    ]

    checker = ConsistencyChecker(threshold=0.5)
    result = checker.evaluate(slice_indicators)

    assert not result.is_consistent
    assert result.inconsistency_score > 0.5
    assert len(result.inconsistent_indicators) > 0


def test_consistency_checker_single_slice():
    """Test that single slice is marked as consistent (no comparison possible)."""
    slice_indicators = [
        {"rms_energy": 0.1, "spectral_centroid_mean": 1500.0},
    ]

    checker = ConsistencyChecker()
    result = checker.evaluate(slice_indicators)

    assert result.is_consistent
    assert result.inconsistency_score == 0.0
    assert len(result.inconsistent_indicators) == 0


def test_consistency_checker_empty_slices():
    """Test that empty slice list is handled gracefully."""
    slice_indicators: list[dict[str, float]] = []

    checker = ConsistencyChecker()
    result = checker.evaluate(slice_indicators)

    assert result.is_consistent
    assert result.inconsistency_score == 0.0
    assert len(result.inconsistent_indicators) == 0


def test_consistency_checker_custom_threshold():
    """Test that custom threshold affects consistency decision."""
    slice_indicators = [
        {"rms_energy": 0.1},
        {"rms_energy": 0.12},  # 20% change
        {"rms_energy": 0.13},
    ]

    # With high threshold (0.5), should be consistent
    checker_high = ConsistencyChecker(threshold=0.5)
    result_high = checker_high.evaluate(slice_indicators)
    assert result_high.is_consistent

    # With low threshold (0.1), should be inconsistent
    checker_low = ConsistencyChecker(threshold=0.1)
    result_low = checker_low.evaluate(slice_indicators)
    assert not result_low.is_consistent


def test_consistency_checker_mixed_indicators():
    """Test that checker handles some consistent and some inconsistent indicators."""
    slice_indicators = [
        {"rms_energy": 0.1, "spectral_centroid_mean": 1500.0},
        {
            "rms_energy": 0.11,
            "spectral_centroid_mean": 4500.0,
        },  # Centroid jumps, RMS stable
        {"rms_energy": 0.09, "spectral_centroid_mean": 1600.0},
    ]

    checker = ConsistencyChecker(threshold=0.5)
    result = checker.evaluate(slice_indicators)

    # Should be inconsistent due to spectral_centroid
    assert not result.is_consistent
    assert "spectral_centroid_mean" in result.inconsistent_indicators
    # RMS should be consistent
    assert "rms_energy" not in result.inconsistent_indicators


def test_consistency_checker_zero_values():
    """Test that checker handles zero values gracefully."""
    slice_indicators = [
        {"rms_energy": 0.0},
        {"rms_energy": 0.1},  # Jump from zero
        {"rms_energy": 0.0},
    ]

    checker = ConsistencyChecker(threshold=0.5)
    result = checker.evaluate(slice_indicators)

    # Should not crash, should return valid result
    assert isinstance(result.is_consistent, bool)
    assert isinstance(result.inconsistency_score, float)
    assert not np.isnan(result.inconsistency_score)
    assert not np.isinf(result.inconsistency_score)


def test_consistency_checker_missing_indicators():
    """Test that checker handles missing indicators in some slices."""
    slice_indicators = [
        {"rms_energy": 0.1, "spectral_centroid_mean": 1500.0},
        {"rms_energy": 0.11},  # Missing spectral_centroid
        {"rms_energy": 0.09, "spectral_centroid_mean": 1600.0},
    ]

    checker = ConsistencyChecker()
    result = checker.evaluate(slice_indicators)

    # Should handle missing values gracefully
    assert isinstance(result.is_consistent, bool)
    assert isinstance(result.inconsistency_score, float)


def test_consistency_checker_multiple_indicators():
    """Test consistency check with many indicators."""
    slice_indicators = [
        {
            "rms_energy": 0.1,
            "spectral_centroid_mean": 1500.0,
            "spectral_flatness_mean": 0.2,
            "crest_factor": 10.0,
        },
        {
            "rms_energy": 0.11,
            "spectral_centroid_mean": 1520.0,
            "spectral_flatness_mean": 0.21,
            "crest_factor": 10.5,
        },
        {
            "rms_energy": 0.09,
            "spectral_centroid_mean": 1480.0,
            "spectral_flatness_mean": 0.19,
            "crest_factor": 9.8,
        },
    ]

    checker = ConsistencyChecker(threshold=0.5)
    result = checker.evaluate(slice_indicators)

    # All indicators are consistent
    assert result.is_consistent
    assert result.inconsistency_score < 0.5
