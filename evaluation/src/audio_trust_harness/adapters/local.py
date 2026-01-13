"""
Local adapter for audio analysis.

Performs all indicator computation locally using the built-in indicators.
This is the default adapter and provides the baseline behavior.
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

from .base import AdapterResult, AdapterStatus, BaseAdapter


class LocalAdapter(BaseAdapter):
    """Local adapter using built-in indicators.

    This adapter performs all audio analysis locally without any
    external dependencies. It uses the full set of indicators:
    - Spectral Centroid
    - Spectral Flatness
    - Spectral Rolloff
    - RMS Energy
    - Crest Factor
    - Zero-Crossing Rate
    """

    def __init__(self):
        """Initialize the local adapter with all built-in indicators."""
        super().__init__("local")
        self._indicators = [
            SpectralCentroidIndicator(),
            SpectralFlatnessIndicator(),
            SpectralRolloffIndicator(),
            RMSEnergyIndicator(),
            CrestFactorIndicator(),
            ZeroCrossingRateIndicator(),
        ]

    def analyze(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        perturbation_name: str | None = None,
    ) -> AdapterResult:
        """Analyze audio using built-in indicators.

        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate in Hz
            perturbation_name: Name of perturbation applied (ignored for local)

        Returns:
            AdapterResult with computed indicator values
        """
        try:
            # Compute all indicators
            all_indicators: dict[str, float] = {}
            for indicator in self._indicators:
                result = indicator.compute(audio_data, sample_rate)
                all_indicators.update(result)

            return AdapterResult(
                status=AdapterStatus.SUCCESS,
                indicators=all_indicators,
                metadata={
                    "adapter": self.name,
                    "indicator_count": len(self._indicators),
                    "perturbation": perturbation_name,
                },
            )
        except Exception as e:
            return AdapterResult(
                status=AdapterStatus.ERROR,
                error_message=str(e),
            )

    def is_available(self) -> bool:
        """Local adapter is always available.

        Returns:
            True (always available)
        """
        return True

    def get_info(self) -> dict:
        """Get information about the local adapter.

        Returns:
            Dictionary with adapter metadata including indicator names
        """
        info = super().get_info()
        info["indicators"] = [ind.name for ind in self._indicators]
        return info
