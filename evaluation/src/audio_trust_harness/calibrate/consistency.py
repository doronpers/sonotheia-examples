"""
Cross-slice consistency checks for temporal coherence.

Evaluates how indicators vary across adjacent slices to detect
temporal inconsistencies that might indicate manipulation.
"""

from dataclasses import dataclass

import numpy as np

from audio_trust_harness.config import CONSISTENCY_CONFIG


@dataclass
class ConsistencyResult:
    """
    Result of cross-slice consistency evaluation.

    Attributes:
        is_consistent: Whether slices show temporal consistency
        inconsistency_score: Overall inconsistency score (0-1, higher = more inconsistent)
        inconsistent_indicators: List of indicator names showing high temporal variation
    """

    is_consistent: bool
    inconsistency_score: float
    inconsistent_indicators: list[str]


class ConsistencyChecker:
    """
    Checks temporal consistency across adjacent slices.

    Compares indicator values between consecutive slices to detect
    abrupt changes that might indicate manipulation.
    """

    def __init__(
        self,
        threshold: float | None = None,
        min_value_threshold: float | None = None,
    ):
        """
        Initialize consistency checker.

        Args:
            threshold: Threshold for temporal variation detection
                      Values above this indicate temporal inconsistency
            min_value_threshold: Minimum value for relative change calculation
                               Values below this use robust change metric
        """
        self.threshold = threshold if threshold is not None else CONSISTENCY_CONFIG.threshold
        self.min_value_threshold = (
            min_value_threshold
            if min_value_threshold is not None
            else CONSISTENCY_CONFIG.min_value_threshold
        )

    def evaluate(self, slice_indicators: list[dict[str, float]]) -> ConsistencyResult:
        """
        Evaluate temporal consistency across slices.

        Args:
            slice_indicators: List of indicator dictionaries, one per slice
                             Each dict maps indicator name to value

        Returns:
            ConsistencyResult object
        """
        if len(slice_indicators) < 2:
            # Need at least 2 slices for consistency check
            return ConsistencyResult(
                is_consistent=True,
                inconsistency_score=0.0,
                inconsistent_indicators=[],
            )

        # Collect all indicator names
        indicator_names: set[str] = set()
        for indicators in slice_indicators:
            indicator_names.update(indicators.keys())

        # Compute temporal variation for each indicator
        temporal_variations = {}
        inconsistent_indicators = []

        for indicator_name in indicator_names:
            # Extract values for this indicator across slices
            values = []
            for indicators in slice_indicators:
                if indicator_name in indicators:
                    values.append(indicators[indicator_name])

            if len(values) < 2:
                # Not enough values for this indicator
                continue

            # Compute normalized changes between consecutive slices
            normalized_changes = []
            for i in range(len(values) - 1):
                curr_val = values[i]
                next_val = values[i + 1]

                # Use symmetric normalized change for robust comparison
                # This works well for both near-zero and non-zero values
                abs_change = abs(next_val - curr_val)

                # Use average of absolute values as reference scale
                reference = (abs(curr_val) + abs(next_val)) / 2.0

                if reference > self.min_value_threshold:
                    # Normal case: normalize by reference scale
                    normalized_change = abs_change / reference
                else:
                    # Near-zero case: use absolute change scaled by threshold
                    # This makes near-zero changes comparable to relative changes
                    normalized_change = abs_change / self.min_value_threshold

                normalized_changes.append(normalized_change)

            # Compute mean normalized change as temporal variation metric
            if normalized_changes:
                temporal_var = float(np.mean(normalized_changes))
                temporal_variations[indicator_name] = temporal_var

                if temporal_var > self.threshold:
                    inconsistent_indicators.append(indicator_name)

        # Overall inconsistency score (max across indicators)
        if temporal_variations:
            inconsistency_score = max(temporal_variations.values())
        else:
            inconsistency_score = 0.0

        # Decision
        is_consistent = len(inconsistent_indicators) == 0

        return ConsistencyResult(
            is_consistent=is_consistent,
            inconsistency_score=float(inconsistency_score),
            inconsistent_indicators=inconsistent_indicators,
        )
