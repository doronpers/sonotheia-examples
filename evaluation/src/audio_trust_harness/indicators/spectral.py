"""
Spectral indicators for audio analysis.

All spectral indicators use Short-Time Fourier Transform (STFT) with
consistent parameters defined in the configuration module for reproducibility.
"""

import numpy as np
from scipy import signal as scipy_signal  # type: ignore

from audio_trust_harness.config import SPECTRAL_CONFIG, STFT_CONFIG

from .base import Indicator


class SpectralCentroidIndicator(Indicator):
    """
    Spectral centroid: weighted mean of frequencies.
    Indicates "brightness" of the sound.
    """

    def __init__(self):
        super().__init__("spectral_centroid")

    def compute(self, audio: np.ndarray, sample_rate: int) -> dict[str, float]:
        """Compute spectral centroid mean and std."""
        # Compute STFT with configured parameters
        f, t, Zxx = scipy_signal.stft(
            audio,
            fs=sample_rate,
            nperseg=STFT_CONFIG.nperseg,
            noverlap=STFT_CONFIG.noverlap,
            window=STFT_CONFIG.window,
        )

        # Magnitude spectrum
        magnitude = np.abs(Zxx)

        # Compute centroid for each frame
        centroids = []
        for frame_idx in range(magnitude.shape[1]):
            frame_mag = magnitude[:, frame_idx]
            if np.sum(frame_mag) > 0:
                centroid = np.sum(f * frame_mag) / np.sum(frame_mag)
                centroids.append(centroid)

        if len(centroids) == 0:
            return {"spectral_centroid_mean": 0.0, "spectral_centroid_std": 0.0}

        return {
            "spectral_centroid_mean": float(np.mean(centroids)),
            "spectral_centroid_std": float(np.std(centroids)),
        }


class SpectralFlatnessIndicator(Indicator):
    """
    Spectral flatness: measure of tonality vs noise-like character.
    0 = pure tone, 1 = white noise.
    """

    def __init__(self):
        super().__init__("spectral_flatness")

    def compute(self, audio: np.ndarray, sample_rate: int) -> dict[str, float]:
        """Compute spectral flatness mean and std."""
        # Compute STFT with configured parameters
        f, t, Zxx = scipy_signal.stft(
            audio,
            fs=sample_rate,
            nperseg=STFT_CONFIG.nperseg,
            noverlap=STFT_CONFIG.noverlap,
            window=STFT_CONFIG.window,
        )

        # Power spectrum
        power = np.abs(Zxx) ** 2

        # Compute flatness for each frame
        flatness_values = []
        for frame_idx in range(power.shape[1]):
            frame_power = power[:, frame_idx]

            # Avoid log of zero using configured threshold
            frame_power = frame_power[frame_power > SPECTRAL_CONFIG.min_power_threshold]

            if len(frame_power) > 0:
                # Geometric mean
                geom_mean = np.exp(np.mean(np.log(frame_power)))
                # Arithmetic mean
                arith_mean = np.mean(frame_power)

                if arith_mean > 0:
                    flatness = geom_mean / arith_mean
                    flatness_values.append(flatness)

        if len(flatness_values) == 0:
            return {"spectral_flatness_mean": 0.0, "spectral_flatness_std": 0.0}

        return {
            "spectral_flatness_mean": float(np.mean(flatness_values)),
            "spectral_flatness_std": float(np.std(flatness_values)),
        }


class SpectralRolloffIndicator(Indicator):
    """
    Spectral Rolloff: Frequency below which 85% of spectral energy is contained.
    Indicates bandwidth and frequency content distribution.
    """

    def __init__(self, rolloff_percent: float | None = None):
        """
        Initialize spectral rolloff indicator.

        Args:
            rolloff_percent: Percentage of energy (default from config: 0.85 for 85%)
        """
        super().__init__("spectral_rolloff")
        self.rolloff_percent = (
            rolloff_percent if rolloff_percent is not None else SPECTRAL_CONFIG.rolloff_percent
        )

    def compute(self, audio: np.ndarray, sample_rate: int) -> dict[str, float]:
        """Compute spectral rolloff mean and std."""
        # Compute STFT with configured parameters
        f, t, Zxx = scipy_signal.stft(
            audio,
            fs=sample_rate,
            nperseg=STFT_CONFIG.nperseg,
            noverlap=STFT_CONFIG.noverlap,
            window=STFT_CONFIG.window,
        )

        # Magnitude spectrum
        magnitude = np.abs(Zxx)

        # Compute rolloff for each frame
        rolloff_values = []
        for frame_idx in range(magnitude.shape[1]):
            frame_mag = magnitude[:, frame_idx]

            # Total energy
            total_energy = np.sum(frame_mag)

            if total_energy > 0:
                # Cumulative energy
                cumulative_energy = np.cumsum(frame_mag)

                # Find frequency where cumulative energy exceeds threshold
                threshold = self.rolloff_percent * total_energy
                rolloff_idx = np.where(cumulative_energy >= threshold)[0]

                if len(rolloff_idx) > 0:
                    rolloff_freq = f[rolloff_idx[0]]
                    rolloff_values.append(rolloff_freq)

        if len(rolloff_values) == 0:
            return {"spectral_rolloff_mean": 0.0, "spectral_rolloff_std": 0.0}

        return {
            "spectral_rolloff_mean": float(np.mean(rolloff_values)),
            "spectral_rolloff_std": float(np.std(rolloff_values)),
        }
