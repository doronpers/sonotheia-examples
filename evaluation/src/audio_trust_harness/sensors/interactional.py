"""
Interactional sensor for voice risk assessment.

Analyzes interactional patterns in audio to detect evidence of
synthetic or manipulated voice characteristics.
"""

import numpy as np
from scipy import signal

from audio_trust_harness.sensors.base import BaseSensor, SensorResult


class InteractionalSensor(BaseSensor):
    """Sensor that analyzes interactional voice patterns.

    Examines temporal dynamics, energy patterns, and spectral characteristics
    to identify evidence of synthetic voice generation or manipulation.
    """

    def __init__(self):
        """Initialize the interactional sensor."""
        super().__init__("interactional")

    def analyze(
        self, audio: np.ndarray, sample_rate: int
    ) -> SensorResult:
        """Analyze interactional patterns in audio.

        Args:
            audio: Audio samples as float32 numpy array
            sample_rate: Sample rate in Hz (expected: 16000)

        Returns:
            SensorResult with interactional risk signals

        Raises:
            ValueError: If audio is invalid
        """
        if len(audio) == 0:
            return SensorResult(
                signals={},
                confidence=0.0,
                reason_codes=["EMPTY_AUDIO"],
                recommended_action="insufficient_evidence",
            )

        if len(audio) < sample_rate * 0.5:  # Less than 0.5 seconds
            return SensorResult(
                signals={},
                confidence=0.3,
                reason_codes=["AUDIO_TOO_SHORT"],
                recommended_action="insufficient_evidence",
            )

        # Compute signals
        signals = self._compute_signals(audio, sample_rate)

        # Compute confidence based on signal consistency
        confidence = self._compute_confidence(signals)

        # Determine reason codes
        reason_codes = self._determine_reason_codes(signals, confidence)

        # Determine recommended action
        recommended_action = self._determine_action(confidence, reason_codes)

        return SensorResult(
            signals=signals,
            confidence=confidence,
            reason_codes=reason_codes,
            recommended_action=recommended_action,
        )

    def _compute_signals(
        self, audio: np.ndarray, sample_rate: int
    ) -> dict[str, float]:
        """Compute interactional signal values.

        Args:
            audio: Audio samples
            sample_rate: Sample rate in Hz

        Returns:
            Dictionary of signal values
        """
        signals = {}

        # Energy-based signals
        rms_energy = np.sqrt(np.mean(audio**2))
        signals["rms_energy"] = float(rms_energy)

        # Zero-crossing rate (interactional dynamics)
        zero_crossings = np.sum(np.diff(np.signbit(audio)))
        zcr = zero_crossings / (2.0 * len(audio)) * sample_rate
        signals["zero_crossing_rate"] = float(zcr)

        # Spectral centroid (brightness)
        freqs, psd = signal.welch(
            audio, sample_rate, nperseg=min(2048, len(audio))
        )
        if np.sum(psd) > 0:
            spectral_centroid = np.sum(freqs * psd) / np.sum(psd)
        else:
            spectral_centroid = 0.0
        signals["spectral_centroid"] = float(spectral_centroid)

        # Temporal variation (interactional dynamics)
        # Compute energy in overlapping windows
        window_size = int(sample_rate * 0.1)  # 100ms windows
        hop_size = window_size // 2
        if len(audio) >= window_size:
            energy_variation = []
            for i in range(0, len(audio) - window_size, hop_size):
                window = audio[i : i + window_size]
                energy = np.sqrt(np.mean(window**2))
                energy_variation.append(energy)
            if len(energy_variation) > 1:
                cv = np.std(energy_variation) / (
                    np.mean(energy_variation) + 1e-10
                )
            else:
                cv = 0.0
        else:
            cv = 0.0
        signals["temporal_variation"] = float(cv)

        # Spectral flatness (tonality measure)
        if np.sum(psd) > 0 and np.all(psd > 0):
            # Avoid log(0)
            geometric_mean = np.exp(np.mean(np.log(psd + 1e-10)))
            arithmetic_mean = np.mean(psd)
            flatness = geometric_mean / (arithmetic_mean + 1e-10)
        else:
            flatness = 0.0
        signals["spectral_flatness"] = float(flatness)

        return signals

    def _compute_confidence(self, signals: dict[str, float]) -> float:
        """Compute confidence score from signals.

        Args:
            signals: Dictionary of signal values

        Returns:
            Confidence score in [0.0, 1.0]
        """
        if not signals:
            return 0.0

        # Base confidence from signal quality
        # Higher temporal variation suggests more natural interaction
        temporal_var = signals.get("temporal_variation", 0.0)
        base_confidence = min(0.7 + temporal_var * 0.3, 1.0)

        # Adjust based on spectral characteristics
        spectral_flatness = signals.get("spectral_flatness", 0.0)
        # Very flat (noise-like) or very tonal (synthetic-like) reduces confidence
        if spectral_flatness < 0.1 or spectral_flatness > 0.9:
            base_confidence *= 0.8

        # Ensure bounds
        return max(0.0, min(1.0, base_confidence))

    def _determine_reason_codes(
        self, signals: dict[str, float], confidence: float
    ) -> list[str]:
        """Determine reason codes from signals and confidence.

        Args:
            signals: Dictionary of signal values
            confidence: Confidence score

        Returns:
            List of reason codes
        """
        reason_codes = []

        if confidence < 0.3:
            reason_codes.append("LOW_CONFIDENCE")

        temporal_var = signals.get("temporal_variation", 0.0)
        if temporal_var < 0.1:
            reason_codes.append("LOW_TEMPORAL_VARIATION")

        spectral_flatness = signals.get("spectral_flatness", 0.0)
        if spectral_flatness > 0.8:
            reason_codes.append("HIGH_SPECTRAL_FLATNESS")

        rms_energy = signals.get("rms_energy", 0.0)
        if rms_energy < 0.01:
            reason_codes.append("LOW_ENERGY")

        return reason_codes

    def _determine_action(
        self, confidence: float, reason_codes: list[str]
    ) -> str:
        """Determine recommended action from confidence and reason codes.

        Args:
            confidence: Confidence score
            reason_codes: List of reason codes

        Returns:
            Recommended action: "accept", "defer_to_review", or "insufficient_evidence"
        """
        if confidence < 0.3 or "LOW_CONFIDENCE" in reason_codes:
            return "insufficient_evidence"

        if confidence < 0.6 or len(reason_codes) >= 2:
            return "defer_to_review"

        return "accept"
