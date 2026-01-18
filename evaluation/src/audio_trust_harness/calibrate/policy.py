"""
Deferral policy for audio slice evaluation.

Rules-based policy (no ML) that compares indicator stability across
perturbations and outputs deferral recommendations.
"""

from dataclasses import dataclass

import numpy as np

from audio_trust_harness.config import DEFERRAL_POLICY_CONFIG


@dataclass
class DeferralDecision:
    """
    Deferral decision for an audio slice.

    Attributes:
        recommended_action: One of 'accept', 'defer_to_review', 'insufficient_evidence'
        fragility_score: Overall fragility score (0-1, higher = more fragile)
        reasons: List of reason tags for the decision
    """

    recommended_action: str
    fragility_score: float
    reasons: list[str]


class DeferralPolicy:
    """
    Rules-based deferral policy.

    Evaluates indicator stability across perturbations and outputs
    deferral recommendations.
    """

    def __init__(
        self,
        fragility_threshold: float | None = None,
        clipping_threshold: float | None = None,
        min_duration: float | None = None,
        min_mean_threshold: float | None = None,
    ):
        """
        Initialize deferral policy.

        Args:
            fragility_threshold: CV threshold for fragility detection
            clipping_threshold: Amplitude threshold for clipping detection
            min_duration: Minimum slice duration in seconds
            min_mean_threshold: Minimum mean value for CV calculation
        """
        # Use config defaults if not specified
        self.fragility_threshold = (
            fragility_threshold
            if fragility_threshold is not None
            else DEFERRAL_POLICY_CONFIG.fragility_threshold
        )
        self.clipping_threshold = (
            clipping_threshold
            if clipping_threshold is not None
            else DEFERRAL_POLICY_CONFIG.clipping_threshold
        )
        self.min_duration = (
            min_duration if min_duration is not None else DEFERRAL_POLICY_CONFIG.min_duration
        )
        self.min_mean_threshold = (
            min_mean_threshold
            if min_mean_threshold is not None
            else DEFERRAL_POLICY_CONFIG.min_mean_threshold
        )

    def evaluate(
        self,
        indicators_by_perturbation: dict[str, dict[str, float]],
        audio_data: np.ndarray,
        sample_rate: int,
        duration: float,
    ) -> DeferralDecision:
        """
        Evaluate a slice and produce a deferral decision.

        Args:
            indicators_by_perturbation: Dict mapping perturbation name to indicator values
            audio_data: Raw audio data (for validation checks)
            sample_rate: Sample rate in Hz
            duration: Slice duration in seconds

        Returns:
            DeferralDecision object
        """
        reasons = []

        # Check for insufficient evidence conditions
        if duration < self.min_duration:
            return DeferralDecision(
                recommended_action="insufficient_evidence",
                fragility_score=0.0,
                reasons=["slice_too_short"],
            )

        # Check for clipping
        if self._is_clipped(audio_data):
            return DeferralDecision(
                recommended_action="insufficient_evidence",
                fragility_score=0.0,
                reasons=["clipping_detected"],
            )

        # Compute fragility scores for each indicator
        fragility_scores, fragile_indicators = self._compute_fragility(indicators_by_perturbation)

        if not fragility_scores:
            # No valid indicators
            return DeferralDecision(
                recommended_action="insufficient_evidence",
                fragility_score=0.0,
                reasons=["no_valid_indicators"],
            )

        # Overall fragility score (max across indicators)
        overall_fragility = max(fragility_scores.values())

        # Check for fragile indicators
        if fragile_indicators:
            reasons.extend([f"high_fragility_{indicator}" for indicator in fragile_indicators])

        # Make decision
        if reasons:
            action = "defer_to_review"
        else:
            action = "accept"

        return DeferralDecision(
            recommended_action=action,
            fragility_score=float(overall_fragility),
            reasons=reasons,
        )

    def _is_clipped(self, audio_data: np.ndarray) -> bool:
        """Check if audio is clipped."""
        max_amp = np.max(np.abs(audio_data))
        return bool(max_amp >= self.clipping_threshold)

    def _compute_fragility(
        self, indicators_by_perturbation: dict[str, dict[str, float]]
    ) -> tuple[dict[str, float], list[str]]:
        """
        Compute fragility scores for each indicator.

        Uses coefficient of variation (CV) for normal cases, and a robust
        metric (normalized IQR) for near-zero means to ensure comparability.

        Returns:
            Tuple of (fragility_scores_dict, list_of_fragile_indicators)
        """
        # Collect indicator values across perturbations
        indicator_values: dict[str, list[float]] = {}

        for perturbation_name, indicators in indicators_by_perturbation.items():
            for indicator_name, value in indicators.items():
                if indicator_name not in indicator_values:
                    indicator_values[indicator_name] = []
                indicator_values[indicator_name].append(value)

        # Compute fragility score for each indicator
        fragility_scores = {}
        fragile_indicators = []

        for indicator_name, values in indicator_values.items():
            if len(values) < 2:
                # Need at least 2 values to compute fragility
                continue

            values_array = np.array(values)
            mean_val = np.mean(values_array)
            std_val = np.std(values_array)

            # Use coefficient of variation for normal cases
            if abs(mean_val) > self.min_mean_threshold:
                fragility = std_val / abs(mean_val)
            else:
                # For near-zero means, use robust metric based on IQR
                # This provides comparable scale to CV
                median_val = np.median(values_array)
                q1 = np.percentile(values_array, 25)
                q3 = np.percentile(values_array, 75)
                iqr = q3 - q1

                # Robust CV: IQR / (median + epsilon)
                # Add epsilon to avoid division by zero
                epsilon = self.min_mean_threshold
                robust_scale = abs(median_val) + epsilon
                fragility = iqr / robust_scale

            fragility_scores[indicator_name] = fragility

            if fragility > self.fragility_threshold:
                fragile_indicators.append(indicator_name)

        return fragility_scores, fragile_indicators
