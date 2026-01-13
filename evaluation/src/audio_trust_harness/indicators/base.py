"""
Base indicator interface.
"""

import numpy as np


class Indicator:
    """Base class for audio indicators."""

    def __init__(self, name: str):
        self.name = name

    def compute(self, audio: np.ndarray, sample_rate: int) -> dict[str, float]:
        """
        Compute indicator values for audio.

        Args:
            audio: Audio samples
            sample_rate: Sample rate in Hz

        Returns:
            Dictionary of indicator values (all numeric)
        """
        raise NotImplementedError
