"""
Temporal (time-domain) indicators for audio analysis.
"""

import numpy as np

from .base import Indicator


class RMSEnergyIndicator(Indicator):
    """
    RMS Energy: Root mean square amplitude.
    Indicates overall loudness.
    """

    def __init__(self):
        super().__init__("rms_energy")

    def compute(self, audio: np.ndarray, sample_rate: int) -> dict[str, float]:
        """Compute RMS energy."""
        rms = np.sqrt(np.mean(audio**2))
        return {"rms_energy": float(rms)}


class CrestFactorIndicator(Indicator):
    """
    Crest Factor: Peak-to-RMS ratio.
    Indicates dynamic range.
    """

    def __init__(self):
        super().__init__("crest_factor")

    def compute(self, audio: np.ndarray, sample_rate: int) -> dict[str, float]:
        """Compute crest factor."""
        peak = np.max(np.abs(audio))
        rms = np.sqrt(np.mean(audio**2))

        if rms > 0:
            crest_factor = peak / rms
        else:
            crest_factor = 0.0

        return {"crest_factor": float(crest_factor)}


class ZeroCrossingRateIndicator(Indicator):
    """
    Zero-Crossing Rate: Rate at which signal changes sign.
    Indicates noisiness and pitch (higher ZCR = higher pitch or more noise).
    """

    def __init__(self):
        super().__init__("zero_crossing_rate")

    def compute(self, audio: np.ndarray, sample_rate: int) -> dict[str, float]:
        """Compute zero-crossing rate."""
        # Count sign changes
        zero_crossings = np.sum(np.abs(np.diff(np.sign(audio)))) / 2

        # Normalize by audio length
        zcr = zero_crossings / len(audio)

        return {"zero_crossing_rate": float(zcr)}
