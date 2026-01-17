"""
Unknown sensor for voice risk assessment.

Analyzes unknown or anomalous patterns in audio that may indicate
synthetic voice generation or manipulation.
"""

import numpy as np
from scipy import signal

from audio_trust_harness.sensors.base import BaseSensor, SensorResult


class UnknownSensor(BaseSensor):
    """Sensor that analyzes unknown/anomalous patterns.

    Examines spectral anomalies, phase coherence, and other indicators
    that may suggest synthetic voice characteristics.
    """

    def __init__(self):
        """Initialize the unknown sensor."""
        super().__init__("unknown")

    def analyze(
        self, audio: np.ndarray, sample_rate: int
    ) -> SensorResult:
        """Analyze unknown patterns in audio.

        Args:
            audio: Audio samples as float32 numpy array
            sample_rate: Sample rate in Hz (expected: 16000)

        Returns:
            SensorResult with unknown risk signals

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
        """Compute unknown pattern signal values.

        Args:
            audio: Audio samples
            sample_rate: Sample rate in Hz

        Returns:
            Dictionary of signal values
        """
        signals = {}

        # Spectral analysis
        freqs, psd = signal.welch(
            audio, sample_rate, nperseg=min(2048, len(audio))
        )

        # Spectral rolloff (frequency below which 85% of energy is contained)
        cumsum_psd = np.cumsum(psd)
        total_energy = cumsum_psd[-1]
        if total_energy > 0:
            rolloff_idx = np.where(cumsum_psd >= 0.85 * total_energy)[0]
            if len(rolloff_idx) > 0:
                spectral_rolloff = float(freqs[rolloff_idx[0]])
            else:
                spectral_rolloff = float(freqs[-1])
        else:
            spectral_rolloff = 0.0
        signals["spectral_rolloff"] = spectral_rolloff

        # Spectral bandwidth (spread of energy)
        if np.sum(psd) > 0:
            spectral_centroid = np.sum(freqs * psd) / np.sum(psd)
            bandwidth = np.sqrt(
                np.sum(((freqs - spectral_centroid) ** 2) * psd)
                / np.sum(psd)
            )
        else:
            bandwidth = 0.0
        signals["spectral_bandwidth"] = float(bandwidth)

        # Phase coherence (using STFT)
        if len(audio) >= 512:
            _, _, stft = signal.stft(
                audio, sample_rate, nperseg=512, noverlap=256
            )
            # Compute phase coherence across time
            phase = np.angle(stft)
            phase_diff = np.diff(phase, axis=1)
            # Measure phase stability
            phase_coherence = float(
                1.0 - np.mean(np.abs(np.sin(phase_diff / 2.0)))
            )
        else:
            phase_coherence = 0.0
        signals["phase_coherence"] = phase_coherence

        # Crest factor (peak-to-RMS ratio)
        rms = np.sqrt(np.mean(audio**2))
        if rms > 0:
            peak = np.max(np.abs(audio))
            crest_factor = float(peak / rms)
        else:
            crest_factor = 0.0
        signals["crest_factor"] = crest_factor

        # Spectral kurtosis (measure of spectral shape)
        if np.sum(psd) > 0 and np.std(psd) > 0:
            mean_psd = np.mean(psd)
            std_psd = np.std(psd)
            kurtosis = float(
                np.mean(((psd - mean_psd) / std_psd) ** 4) - 3.0
            )
        else:
            kurtosis = 0.0
        signals["spectral_kurtosis"] = kurtosis

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
        base_confidence = 0.6

        # Adjust based on phase coherence (higher = more natural)
        phase_coherence = signals.get("phase_coherence", 0.0)
        base_confidence += phase_coherence * 0.2

        # Adjust based on spectral characteristics
        spectral_bandwidth = signals.get("spectral_bandwidth", 0.0)
        # Very narrow or very wide bandwidth may indicate issues
        if 500 < spectral_bandwidth < 3000:
            base_confidence += 0.1
        elif spectral_bandwidth < 200 or spectral_bandwidth > 5000:
            base_confidence -= 0.1

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

        phase_coherence = signals.get("phase_coherence", 0.0)
        if phase_coherence < 0.3:
            reason_codes.append("LOW_PHASE_COHERENCE")

        spectral_bandwidth = signals.get("spectral_bandwidth", 0.0)
        if spectral_bandwidth < 200:
            reason_codes.append("NARROW_BANDWIDTH")
        elif spectral_bandwidth > 5000:
            reason_codes.append("WIDE_BANDWIDTH")

        spectral_kurtosis = signals.get("spectral_kurtosis", 0.0)
        if abs(spectral_kurtosis) > 5.0:
            reason_codes.append("ANOMALOUS_SPECTRAL_SHAPE")

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
