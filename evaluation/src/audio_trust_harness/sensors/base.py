"""
Base sensor interface for evidence-first voice risk assessment.

All sensors must implement this interface to produce deterministic,
public-safe risk signals.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class SensorResult:
    """Result from a sensor analysis.

    Attributes:
        signals: Dictionary of signal values (evidence indicators)
        confidence: Confidence score from 0.0 to 1.0
        reason_codes: List of reason codes explaining the assessment
        recommended_action: Recommended action based on evidence
        metadata: Additional metadata (optional)
    """

    signals: dict[str, float]
    confidence: float
    reason_codes: list[str]
    recommended_action: str
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        """Validate result after initialization."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be in [0.0, 1.0], got {self.confidence}"
            )
        if not isinstance(self.signals, dict):
            raise TypeError(f"signals must be dict, got {type(self.signals)}")
        if not isinstance(self.reason_codes, list):
            raise TypeError(
                f"reason_codes must be list, got {type(self.reason_codes)}"
            )


class BaseSensor(ABC):
    """Base class for all voice risk assessment sensors.

    Sensors analyze audio and produce evidence-based risk signals
    without making claims of certainty. All sensors must be:
    - Deterministic (same input → same output)
    - Public-safe (no raw audio bytes, no base64)
    - Evidence-first (signals + confidence, not binary decisions)
    """

    def __init__(self, name: str):
        """Initialize the sensor.

        Args:
            name: Human-readable name for this sensor
        """
        self.name = name

    @abstractmethod
    def analyze(
        self, audio: np.ndarray, sample_rate: int
    ) -> SensorResult:
        """Analyze audio and return risk assessment.

        Args:
            audio: Audio samples as float32 numpy array
            sample_rate: Sample rate in Hz (expected: 16000)

        Returns:
            SensorResult with signals, confidence, reason_codes, and action

        Raises:
            ValueError: If audio is invalid (empty, wrong format, etc.)
        """
        raise NotImplementedError

    def get_info(self) -> dict[str, Any]:
        """Get information about this sensor.

        Returns:
            Dictionary with sensor metadata
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
        }
