"""
Base adapter interface for production API integrations.

Adapters provide a uniform interface for different audio analysis backends,
enabling seamless switching between local processing and external APIs.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class AdapterStatus(Enum):
    """Status of an adapter response."""

    SUCCESS = "success"
    ERROR = "error"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"


@dataclass
class AdapterResult:
    """Result from an adapter operation.

    Attributes:
        status: Status of the operation
        indicators: Dictionary of computed indicator values (if successful)
        deferral_action: Recommended deferral action (if provided by adapter)
        confidence: Confidence score from 0-1 (if provided by adapter)
        metadata: Additional metadata from the adapter
        error_message: Error message if status is ERROR
    """

    status: AdapterStatus
    indicators: dict[str, float] | None = None
    deferral_action: str | None = None
    confidence: float | None = None
    metadata: dict | None = None
    error_message: str | None = None


class BaseAdapter(ABC):
    """Abstract base class for audio analysis adapters.

    Adapters encapsulate the logic for analyzing audio and returning
    indicator values. This allows the same harness to work with:
    - Local indicator computation (default)
    - Remote API services
    - Hybrid approaches

    All adapters must implement the analyze() method.
    """

    def __init__(self, name: str):
        """Initialize the adapter.

        Args:
            name: Human-readable name for this adapter
        """
        self.name = name

    @abstractmethod
    def analyze(
        self,
        audio_data: np.ndarray,  # noqa: F821
        sample_rate: int,
        perturbation_name: str | None = None,
    ) -> AdapterResult:
        """Analyze audio and return indicator values.

        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate in Hz
            perturbation_name: Name of perturbation applied (if any)

        Returns:
            AdapterResult with computed indicators or error information
        """
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this adapter is currently available.

        Returns:
            True if the adapter can process requests
        """
        raise NotImplementedError

    def get_info(self) -> dict:
        """Get information about this adapter.

        Returns:
            Dictionary with adapter metadata
        """
        return {
            "name": self.name,
            "available": self.is_available(),
            "type": self.__class__.__name__,
        }
