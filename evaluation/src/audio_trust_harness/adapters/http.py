"""
HTTP adapter for external API integrations.

Provides a framework for integrating with external audio analysis APIs.
This adapter handles HTTP communication, authentication, and response parsing.
"""

import base64
import io
from dataclasses import dataclass, field

import numpy as np
import soundfile as sf  # type: ignore

from .base import AdapterResult, AdapterStatus, BaseAdapter


@dataclass
class HTTPAdapterConfig:
    """Configuration for HTTP adapter.

    Attributes:
        base_url: Base URL of the API endpoint
        api_key: API key for authentication (optional)
        timeout_seconds: Request timeout in seconds
        headers: Additional headers to include in requests
        verify_ssl: Whether to verify SSL certificates
    """

    base_url: str
    api_key: str | None = None
    timeout_seconds: float = 30.0
    headers: dict[str, str] = field(default_factory=dict)
    verify_ssl: bool = True


class HTTPAdapter(BaseAdapter):
    """HTTP adapter for external API integration.

    This adapter sends audio data to an external API for analysis.
    It supports:
    - Base64-encoded audio payloads
    - API key authentication
    - Configurable timeouts and headers
    - Response parsing for indicator extraction

    Example usage:
        config = HTTPAdapterConfig(
            base_url="https://api.example.com/analyze",
            api_key="your-api-key",
        )
        adapter = HTTPAdapter(config)
        result = adapter.analyze(audio_data, sample_rate)
    """

    def __init__(self, config: HTTPAdapterConfig):
        """Initialize the HTTP adapter.

        Args:
            config: Configuration for the adapter
        """
        super().__init__("http")
        self.config = config
        self._available: bool | None = None

    def _encode_audio(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """Encode audio data as base64 WAV.

        Args:
            audio_data: Audio samples
            sample_rate: Sample rate in Hz

        Returns:
            Base64-encoded WAV data
        """
        buffer = io.BytesIO()
        sf.write(buffer, audio_data, sample_rate, format="WAV", subtype="FLOAT")
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("utf-8")

    def _build_headers(self) -> dict[str, str]:
        """Build request headers including authentication.

        Returns:
            Dictionary of headers
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        headers.update(self.config.headers)

        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        return headers

    def _parse_response(self, response_data: dict) -> AdapterResult:
        """Parse API response into AdapterResult.

        Override this method to handle custom API response formats.

        Args:
            response_data: Parsed JSON response from API

        Returns:
            AdapterResult with extracted data
        """
        # Default parsing assumes standard response format:
        # {
        #   "indicators": {...},
        #   "deferral_action": "accept|defer_to_review|insufficient_evidence",
        #   "confidence": 0.0-1.0,
        #   "metadata": {...}
        # }
        return AdapterResult(
            status=AdapterStatus.SUCCESS,
            indicators=response_data.get("indicators"),
            deferral_action=response_data.get("deferral_action"),
            confidence=response_data.get("confidence"),
            metadata=response_data.get("metadata"),
        )

    def analyze(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        perturbation_name: str | None = None,
    ) -> AdapterResult:
        """Analyze audio by sending to external API.

        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate in Hz
            perturbation_name: Name of perturbation applied

        Returns:
            AdapterResult from the API or error information
        """
        try:
            import requests
        except ImportError:
            return AdapterResult(
                status=AdapterStatus.UNAVAILABLE,
                error_message="requests library not installed. Install with: pip install requests",
            )

        try:
            # Encode audio
            audio_b64 = self._encode_audio(audio_data, sample_rate)

            # Build payload
            payload = {
                "audio": audio_b64,
                "sample_rate": sample_rate,
                "format": "wav",
            }
            if perturbation_name:
                payload["perturbation"] = perturbation_name

            # Make request
            response = requests.post(
                self.config.base_url,
                json=payload,
                headers=self._build_headers(),
                timeout=self.config.timeout_seconds,
                verify=self.config.verify_ssl,
            )

            # Handle rate limiting
            if response.status_code == 429:
                return AdapterResult(
                    status=AdapterStatus.RATE_LIMITED,
                    error_message="API rate limit exceeded",
                    metadata={"retry_after": response.headers.get("Retry-After")},
                )

            # Handle errors
            if not response.ok:
                return AdapterResult(
                    status=AdapterStatus.ERROR,
                    error_message=f"API error: {response.status_code} - {response.text}",
                )

            # Parse response
            return self._parse_response(response.json())

        except requests.exceptions.Timeout:
            return AdapterResult(
                status=AdapterStatus.ERROR,
                error_message=f"Request timeout after {self.config.timeout_seconds}s",
            )
        except requests.exceptions.ConnectionError as e:
            return AdapterResult(
                status=AdapterStatus.UNAVAILABLE,
                error_message=f"Connection error: {e}",
            )
        except Exception as e:
            return AdapterResult(
                status=AdapterStatus.ERROR,
                error_message=f"Unexpected error: {e}",
            )

    def is_available(self) -> bool:
        """Check if the API endpoint is reachable.

        Performs a lightweight check to verify connectivity.
        Result is cached to avoid repeated checks.

        Returns:
            True if the API is reachable
        """
        if self._available is not None:
            return self._available

        try:
            import requests

            # Try a HEAD request to check connectivity
            response = requests.head(
                self.config.base_url,
                headers=self._build_headers(),
                timeout=5.0,
                verify=self.config.verify_ssl,
            )
            self._available = response.status_code < 500
        except Exception:
            self._available = False

        return self._available

    def reset_availability(self) -> None:
        """Reset cached availability status.

        Call this to force a fresh availability check.
        """
        self._available = None

    def get_info(self) -> dict:
        """Get information about the HTTP adapter.

        Returns:
            Dictionary with adapter metadata (excludes sensitive data)
        """
        info = super().get_info()
        info["base_url"] = self.config.base_url
        info["timeout_seconds"] = self.config.timeout_seconds
        info["has_api_key"] = self.config.api_key is not None
        return info
