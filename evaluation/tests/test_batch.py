"""
Tests for batch processing.
"""

import numpy as np
import pytest

from audio_trust_harness.audio import AudioSlice
from audio_trust_harness.batch import (
    derive_seed,
    process_slice,
    process_slices_parallel,
    process_slices_serial,
)


@pytest.fixture
def sample_slices():
    """Create sample audio slices for testing."""
    sr = 16000
    duration = 1.0

    # Create 3 test slices
    slices = []
    for i in range(3):
        # Generate sine wave
        t = np.linspace(0, duration, int(sr * duration))
        audio = np.sin(2 * np.pi * 440 * t) * 0.5

        slice_obj = AudioSlice(
            data=audio,
            sample_rate=sr,
            slice_index=i,
            start_time=float(i * duration),
            duration=duration,
        )
        slices.append(slice_obj)

    return slices


def test_process_slice(sample_slices):
    """Test processing a single slice."""
    slice_obj = sample_slices[0]
    perturbation_names = ["none", "noise"]
    seed = 1337

    result = process_slice(slice_obj, perturbation_names, seed)

    # Check result structure
    assert "slice_index" in result
    assert "indicators_by_perturbation" in result
    assert "perturbation_objects" in result
    assert "deferral_action" in result
    assert "fragility_score" in result

    # Check perturbations were applied
    assert "none" in result["indicators_by_perturbation"]
    assert "noise" in result["indicators_by_perturbation"]

    # Check indicators were computed
    indicators = result["indicators_by_perturbation"]["none"]
    assert "rms_energy" in indicators
    assert "spectral_centroid_mean" in indicators
    assert "zero_crossing_rate" in indicators
    assert "spectral_rolloff_mean" in indicators


def test_process_slices_serial(sample_slices):
    """Test serial processing of multiple slices."""
    perturbation_names = ["none", "noise"]
    seed = 1337

    results = process_slices_serial(sample_slices, perturbation_names, seed)

    # Check we got results for all slices
    assert len(results) == len(sample_slices)

    # Check each result
    for i, result in enumerate(results):
        assert result["slice_index"] == i
        assert "none" in result["indicators_by_perturbation"]
        assert "noise" in result["indicators_by_perturbation"]


def test_process_slices_parallel(sample_slices):
    """Test parallel processing of multiple slices."""
    perturbation_names = ["none", "noise"]
    seed = 1337

    results = process_slices_parallel(sample_slices, perturbation_names, seed, workers=2)

    # Check we got results for all slices
    assert len(results) == len(sample_slices)

    # Check each result
    for result in results:
        assert "slice_index" in result
        assert "none" in result["indicators_by_perturbation"]
        assert "noise" in result["indicators_by_perturbation"]


def test_process_slices_parallel_deterministic(sample_slices):
    """Test that parallel processing is deterministic with same seed."""
    perturbation_names = ["none", "noise"]
    seed = 1337

    # Run twice with same seed
    results1 = process_slices_parallel(sample_slices, perturbation_names, seed, workers=2)
    results2 = process_slices_parallel(sample_slices, perturbation_names, seed, workers=2)

    # Results should be identical (order might vary, so compare by slice_index)
    results1_sorted = sorted(results1, key=lambda r: r["slice_index"])
    results2_sorted = sorted(results2, key=lambda r: r["slice_index"])

    for r1, r2 in zip(results1_sorted, results2_sorted):
        assert r1["slice_index"] == r2["slice_index"]
        # Check indicators are close (not exact due to floating point)
        for key in r1["indicators_by_perturbation"]["none"]:
            val1 = r1["indicators_by_perturbation"]["none"][key]
            val2 = r2["indicators_by_perturbation"]["none"][key]
            assert abs(val1 - val2) < 1e-6


def test_process_slices_serial_vs_parallel(sample_slices):
    """Test that serial and parallel produce same results."""
    perturbation_names = ["none"]
    seed = 1337

    results_serial = process_slices_serial(sample_slices, perturbation_names, seed)
    results_parallel = process_slices_parallel(sample_slices, perturbation_names, seed, workers=2)

    # Results should be identical (order might vary, so compare by slice_index)
    results_serial_sorted = sorted(results_serial, key=lambda r: r["slice_index"])
    results_parallel_sorted = sorted(results_parallel, key=lambda r: r["slice_index"])

    for rs, rp in zip(results_serial_sorted, results_parallel_sorted):
        assert rs["slice_index"] == rp["slice_index"]
        # Check indicators are close
        for key in rs["indicators_by_perturbation"]["none"]:
            val_serial = rs["indicators_by_perturbation"]["none"][key]
            val_parallel = rp["indicators_by_perturbation"]["none"][key]
            assert abs(val_serial - val_parallel) < 1e-6


def test_process_slice_with_multiple_perturbations(sample_slices):
    """Test processing with multiple perturbations."""
    slice_obj = sample_slices[0]
    perturbation_names = ["none", "noise", "codec_stub"]
    seed = 1337

    result = process_slice(slice_obj, perturbation_names, seed)

    # Check all perturbations were applied
    assert "none" in result["indicators_by_perturbation"]
    assert "noise" in result["indicators_by_perturbation"]
    assert "codec_stub" in result["indicators_by_perturbation"]

    # Check fragility score was computed
    assert result["fragility_score"] >= 0.0


def test_process_slice_invalid_perturbation(sample_slices):
    """Test that invalid perturbations are handled gracefully."""
    slice_obj = sample_slices[0]
    perturbation_names = ["none", "invalid_perturbation"]
    seed = 1337

    result = process_slice(slice_obj, perturbation_names, seed)

    # Should still process valid perturbation
    assert "none" in result["indicators_by_perturbation"]
    # Invalid perturbation should be skipped
    assert "invalid_perturbation" not in result["indicators_by_perturbation"]


def test_derive_seed_is_stable_and_unique_per_slice_and_perturbation():
    """Ensure seed derivation is deterministic yet distinct per slice/perturbation."""
    base_seed = 1337

    seed_a = derive_seed(base_seed, slice_index=0, perturbation_name="noise")
    seed_b = derive_seed(base_seed, slice_index=0, perturbation_name="noise")
    seed_c = derive_seed(base_seed, slice_index=1, perturbation_name="noise")
    seed_d = derive_seed(base_seed, slice_index=0, perturbation_name="codec_stub")

    assert seed_a == seed_b  # deterministic
    assert seed_a != seed_c  # changes with slice
    assert seed_a != seed_d  # changes with perturbation
