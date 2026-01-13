"""
Batch processing for audio slices.

Supports both serial and parallel processing of audio slices.
"""

import multiprocessing as mp
import traceback
import zlib
from typing import Any

from audio_trust_harness.audio import AudioSlice
from audio_trust_harness.calibrate import DeferralPolicy
from audio_trust_harness.indicators import (
    CrestFactorIndicator,
    RMSEnergyIndicator,
    SpectralCentroidIndicator,
    SpectralFlatnessIndicator,
    SpectralRolloffIndicator,
    ZeroCrossingRateIndicator,
)
from audio_trust_harness.perturb import get_perturbation


def process_slice(
    slice_obj: AudioSlice,
    perturbation_names: list[str],
    seed: int,
    fragility_threshold: float = 0.3,
    clipping_threshold: float = 0.95,
    min_duration: float = 0.5,
) -> dict[str, Any]:
    """
    Process a single audio slice with perturbations.

    Args:
        slice_obj: Audio slice to process
        perturbation_names: List of perturbation names to apply
        seed: Random seed for deterministic perturbations
        fragility_threshold: CV threshold for fragility detection (default: 0.3)
        clipping_threshold: Amplitude threshold for clipping detection (default: 0.95)
        min_duration: Minimum slice duration in seconds (default: 0.5)

    Returns:
        Dictionary with processed results
    """
    # Initialize indicators
    indicators_list = [
        SpectralCentroidIndicator(),
        SpectralFlatnessIndicator(),
        SpectralRolloffIndicator(),
        RMSEnergyIndicator(),
        CrestFactorIndicator(),
        ZeroCrossingRateIndicator(),
    ]

    # Initialize deferral policy with custom thresholds
    policy = DeferralPolicy(
        fragility_threshold=fragility_threshold,
        clipping_threshold=clipping_threshold,
        min_duration=min_duration,
    )

    # Store indicators for all perturbations
    indicators_by_perturbation = {}
    perturbation_objects = {}
    errors = []

    # Apply each perturbation
    for perturbation_name in perturbation_names:
        try:
            # Get perturbation with a derived, deterministic seed so every
            # slice/perturbation pairing receives unique but reproducible noise.
            perturbation_seed = derive_seed(
                seed, slice_obj.slice_index, perturbation_name
            )
            perturbation = get_perturbation(perturbation_name, seed=perturbation_seed)

            # Apply perturbation
            perturbed_audio = perturbation.apply(slice_obj.data, slice_obj.sample_rate)

            # Compute indicators
            indicators = {}
            for indicator in indicators_list:
                indicator_values = indicator.compute(
                    perturbed_audio, slice_obj.sample_rate
                )
                indicators.update(indicator_values)

            indicators_by_perturbation[perturbation_name] = indicators
            perturbation_objects[perturbation_name] = perturbation

        except Exception as e:
            # Track error with full context
            error_msg = (
                f"Failed to process {perturbation_name} for slice {slice_obj.slice_index}: "
                f"{type(e).__name__}: {e}"
            )
            errors.append(error_msg)
            print(f"Warning: {error_msg}")
            # Continue with other perturbations
            continue

    # Compute deferral decision
    try:
        deferral = policy.evaluate(
            indicators_by_perturbation,
            slice_obj.data,
            slice_obj.sample_rate,
            slice_obj.duration,
        )
    except Exception as e:
        # If deferral evaluation fails, create a default decision
        error_msg = f"Failed to evaluate deferral policy for slice {slice_obj.slice_index}: {type(e).__name__}: {e}"
        errors.append(error_msg)
        print(f"Warning: {error_msg}")

        # Create a fallback decision
        from audio_trust_harness.calibrate import DeferralDecision

        deferral = DeferralDecision(
            recommended_action="insufficient_evidence",
            fragility_score=0.0,
            reasons=["evaluation_error"],
        )

    result = {
        "slice_index": slice_obj.slice_index,
        "slice_start_s": slice_obj.start_time,
        "slice_duration_s": slice_obj.duration,
        "sample_rate": slice_obj.sample_rate,
        "indicators_by_perturbation": indicators_by_perturbation,
        "perturbation_objects": perturbation_objects,
        "deferral_action": deferral.recommended_action,
        "fragility_score": deferral.fragility_score,
        "reasons": deferral.reasons,
    }

    # Add errors if any occurred
    if errors:
        result["errors"] = errors

    return result


def process_slices_serial(
    slices: list[AudioSlice],
    perturbation_names: list[str],
    seed: int,
    fragility_threshold: float = 0.3,
    clipping_threshold: float = 0.95,
    min_duration: float = 0.5,
) -> list[dict[str, Any]]:
    """
    Process slices serially (one at a time).

    Args:
        slices: List of audio slices to process
        perturbation_names: List of perturbation names to apply
        seed: Random seed for deterministic perturbations
        fragility_threshold: CV threshold for fragility detection (default: 0.3)
        clipping_threshold: Amplitude threshold for clipping detection (default: 0.95)
        min_duration: Minimum slice duration in seconds (default: 0.5)

    Returns:
        List of processing results, one per slice
    """
    results = []
    for slice_obj in slices:
        result = process_slice(
            slice_obj,
            perturbation_names,
            seed,
            fragility_threshold,
            clipping_threshold,
            min_duration,
        )
        results.append(result)
    return results


def process_slices_parallel(
    slices: list[AudioSlice],
    perturbation_names: list[str],
    seed: int,
    workers: int | None = None,
    fragility_threshold: float = 0.3,
    clipping_threshold: float = 0.95,
    min_duration: float = 0.5,
) -> list[dict[str, Any]]:
    """
    Process slices in parallel using multiprocessing.

    Args:
        slices: List of audio slices to process
        perturbation_names: List of perturbation names to apply
        seed: Random seed for deterministic perturbations
        workers: Number of worker processes (default: CPU count)
        fragility_threshold: CV threshold for fragility detection (default: 0.3)
        clipping_threshold: Amplitude threshold for clipping detection (default: 0.95)
        min_duration: Minimum slice duration in seconds (default: 0.5)

    Returns:
        List of processing results, one per slice

    Raises:
        RuntimeError: If parallel processing fails
    """
    if workers is None:
        workers = mp.cpu_count()

    try:
        # Create process pool
        with mp.Pool(processes=workers) as pool:
            # Use starmap to pass multiple arguments
            results = pool.starmap(
                process_slice,
                [
                    (
                        slice_obj,
                        perturbation_names,
                        seed,
                        fragility_threshold,
                        clipping_threshold,
                        min_duration,
                    )
                    for slice_obj in slices
                ],
            )

        # Check for any None results which indicate failures
        failed_slices = [i for i, result in enumerate(results) if result is None]

        if failed_slices:
            print(
                f"Warning: {len(failed_slices)} slices failed to process: {failed_slices}"
            )

        # Filter out None results
        results = [r for r in results if r is not None]

        return results

    except Exception as e:
        error_msg = f"Parallel processing failed: {type(e).__name__}: {e}"
        print(f"Error: {error_msg}")
        print(traceback.format_exc())
        raise RuntimeError(error_msg) from e


def derive_seed(base_seed: int, slice_index: int, perturbation_name: str) -> int:
    """Derive a deterministic seed per slice and perturbation.

    Uses adler32 for stability across Python processes and runs while ensuring
    each slice/perturbation pairing receives distinct randomness without
    sacrificing reproducibility.
    """

    seed_material = f"{base_seed}:{slice_index}:{perturbation_name}".encode()
    return int(zlib.adler32(seed_material) & 0xFFFFFFFF)
