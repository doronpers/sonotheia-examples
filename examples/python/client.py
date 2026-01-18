"""
Sonotheia API client wrapper using requests.

This module provides a simple Python client for the Sonotheia voice fraud detection API,
including deepfake detection, voice MFA verification, and SAR submission.
"""

from __future__ import annotations

import json
import logging
import mimetypes
import os
from typing import IO, Any

import requests
from response_validator import ResponseValidationError, ResponseValidator
from utils import convert_numpy_types

logger = logging.getLogger(__name__)


class SonotheiaClient:
    """Client for Sonotheia voice fraud detection API."""

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        deepfake_path: str | None = None,
        mfa_path: str | None = None,
        sar_path: str | None = None,
        timeout: int = 30,
        validate_responses: bool = True,
    ):
        """
        Initialize Sonotheia API client.

        Args:
            api_key: API key for authentication (defaults to SONOTHEIA_API_KEY env var)
            api_url: Base API URL (defaults to SONOTHEIA_API_URL env var or https://api.sonotheia.com)
            deepfake_path: Deepfake endpoint path (defaults to SONOTHEIA_DEEPFAKE_PATH or /v1/voice/deepfake)
            mfa_path: MFA endpoint path (defaults to SONOTHEIA_MFA_PATH or /v1/mfa/voice/verify)
            sar_path: SAR endpoint path (defaults to SONOTHEIA_SAR_PATH or /v1/reports/sar)
            timeout: Request timeout in seconds (default: 30)
            validate_responses: Enable response validation (default: True)
        """
        self.api_key = api_key or os.getenv("SONOTHEIA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Set SONOTHEIA_API_KEY environment variable or pass api_key parameter."
            )

        self.api_url = (
            api_url or os.getenv("SONOTHEIA_API_URL", "https://api.sonotheia.com")
        ).rstrip("/")
        self.deepfake_path = deepfake_path or os.getenv(
            "SONOTHEIA_DEEPFAKE_PATH", "/v1/voice/deepfake"
        )
        self.mfa_path = mfa_path or os.getenv("SONOTHEIA_MFA_PATH", "/v1/mfa/voice/verify")
        self.sar_path = sar_path or os.getenv("SONOTHEIA_SAR_PATH", "/v1/reports/sar")
        self.timeout = timeout
        self.validate_responses = validate_responses
        self.validator = ResponseValidator() if validate_responses else None

    def _headers(self) -> dict[str, str]:
        """Get common request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

    def _audio_part(self, audio_path: str, file_obj: IO[bytes]) -> tuple[str, Any, str]:
        """
        Prepare audio file part for multipart upload.

        Args:
            audio_path: Path to audio file
            file_obj: Opened binary file handle for the audio content

        Returns:
            Tuple of (filename, file_handle, mime_type)
        """
        mime_type, _ = mimetypes.guess_type(audio_path)
        return (
            os.path.basename(audio_path),
            file_obj,
            mime_type or "application/octet-stream",
        )

    def detect_deepfake(
        self, audio_path: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Detect if audio contains a deepfake.

        Args:
            audio_path: Path to audio file (WAV, Opus, MP3, or FLAC)
            metadata: Optional metadata dict (e.g., session_id, channel)

        Returns:
            Response dict with keys: score, label, latency_ms, session_id (optional)

        Raises:
            requests.HTTPError: If API returns an error status code
            requests.RequestException: For network/connection errors
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        url = f"{self.api_url}{self.deepfake_path}"

        with open(audio_path, "rb") as audio_file:
            files = {"audio": self._audio_part(audio_path, audio_file)}
            safe_metadata = convert_numpy_types(metadata or {})
            data = {"metadata": json.dumps(safe_metadata)}

            response = requests.post(
                url,
                headers=self._headers(),
                files=files,
                data=data,
                timeout=self.timeout,
            )

        response.raise_for_status()
        result = response.json()

        # Validate response if enabled
        if self.validator:
            try:
                result = self.validator.validate_deepfake_response(result)
            except ResponseValidationError as e:
                logger.warning(f"Response validation failed: {e}")
                # Still return the response, but log the validation error

        return result

    def verify_mfa(
        self,
        audio_path: str,
        enrollment_id: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Verify caller identity via voice MFA.

        Args:
            audio_path: Path to audio file
            enrollment_id: Enrollment/voiceprint identifier for the caller
            context: Optional context dict (e.g., session_id, channel)

        Returns:
            Response dict with keys: verified, enrollment_id, confidence, session_id (optional)

        Raises:
            FileNotFoundError: If audio file does not exist
            requests.HTTPError: If API returns an error status code
            requests.RequestException: For network/connection errors
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        url = f"{self.api_url}{self.mfa_path}"

        with open(audio_path, "rb") as audio_file:
            files = {"audio": self._audio_part(audio_path, audio_file)}
            safe_context = convert_numpy_types(context or {})
            data = {
                "enrollment_id": enrollment_id,
                "context": json.dumps(safe_context),
            }

            response = requests.post(
                url,
                headers=self._headers(),
                files=files,
                data=data,
                timeout=self.timeout,
            )

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.error(f"MFA verification failed: {e}")
            raise

        result = response.json()

        # Validate response if enabled
        if self.validator:
            try:
                result = self.validator.validate_mfa_response(result)
            except ResponseValidationError as e:
                logger.warning(f"Response validation failed: {e}")

        return result

    def submit_sar(
        self,
        session_id: str,
        decision: str,
        reason: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Submit a Suspicious Activity Report (SAR).

        Args:
            session_id: Session identifier to link with prior API calls
            decision: Decision type - 'allow', 'deny', or 'review'
            reason: Human-readable reason for the SAR
            metadata: Optional metadata dict

        Returns:
            Response dict with keys: status, case_id, session_id

        Raises:
            requests.HTTPError: If API returns an error status code
            requests.RequestException: For network/connection errors
        """
        url = f"{self.api_url}{self.sar_path}"

        payload = {
            "session_id": session_id,
            "decision": decision,
            "reason": reason,
            "metadata": convert_numpy_types(metadata or {}),
        }

        response = requests.post(
            url,
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )

        response.raise_for_status()
        result = response.json()

        # Validate response if enabled
        if self.validator:
            try:
                result = self.validator.validate_sar_response(result)
            except ResponseValidationError as e:
                logger.warning(f"Response validation failed: {e}")

        return result
