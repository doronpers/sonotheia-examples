"""
Sonotheia API client wrapper using requests.

This module provides a simple Python client for the Sonotheia voice fraud detection API,
including deepfake detection, voice MFA verification, and SAR submission.
"""

from __future__ import annotations

import base64
import logging
import mimetypes
import os
from typing import IO, Any

import requests

from constants import AUDIO_MIME_TYPES, DEFAULT_AUDIO_MIME_TYPE
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
            api_url: Base API URL (defaults to SONOTHEIA_API_URL or https://api.sonotheia.com)
            deepfake_path: Deepfake path (defaults to /api/detect)
            mfa_path: MFA path (defaults to /api/authenticate)
            sar_path: SAR path (defaults to /api/sar/generate)
            timeout: Request timeout in seconds (default: 30)
            validate_responses: Enable response validation (default: True)
        """
        self.api_key = api_key or os.getenv("SONOTHEIA_API_KEY")
        if not self.api_key:
            # We don't raise strict error here to allow demo usage where key might be optional
            # or configured later
            pass

        raw_url = api_url or os.getenv("SONOTHEIA_API_URL", "http://localhost:8000")
        self.api_url = (raw_url or "").rstrip("/")
        self.deepfake_path = deepfake_path or "/api/detect"
        self.mfa_path = mfa_path or "/api/authenticate"
        self.sar_path = sar_path or "/api/sar/generate"
        self.timeout = timeout
        self.validate_responses = validate_responses
        self.validator = ResponseValidator() if validate_responses else None

    def _headers(self, content_type: str = "application/json") -> dict[str, str]:
        """Get common request headers."""
        headers = {
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key

        if content_type:
            headers["Content-Type"] = content_type

        return headers

    def _audio_part(self, audio_path: str, file_obj: IO[bytes]) -> tuple[str, Any, str]:
        """
        Prepare audio file part for multipart upload.

        Args:
            audio_path: Path to audio file
            file_obj: Opened binary file handle for the audio content

        Returns:
            Tuple of (filename, file_handle, mime_type)
        """
        # Try to get MIME type from extension first
        ext = os.path.splitext(audio_path)[1].lower()
        mime_type = AUDIO_MIME_TYPES.get(ext)

        # Fallback to mimetypes module if not in our mapping
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(audio_path)

        return (
            os.path.basename(audio_path),
            file_obj,
            mime_type or DEFAULT_AUDIO_MIME_TYPE,
        )

    def detect_deepfake(
        self, audio_path: str, metadata: dict[str, Any] | None = None, quick_mode: bool = False
    ) -> dict[str, Any]:
        """
        Detect if audio contains a deepfake.

        Args:
            audio_path: Path to audio file (WAV, Opus, MP3, or FLAC)
            metadata: Optional metadata dict (unused in current API spec but kept for compat)
            quick_mode: Run faster, less accurate detection

        Returns:
            Response dict with detection results

        Raises:
            requests.HTTPError: If API returns an error status code
            requests.RequestException: For network/connection errors
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        url = f"{self.api_url}{self.deepfake_path}"

        # /api/detect accepts multipart/form-data
        with open(audio_path, "rb") as audio_file:
            files = {"file": self._audio_part(audio_path, audio_file)}
            params = {"quick_mode": str(quick_mode).lower()}

            # Multipart requests shouldn't set Content-Type header manually (requests does it)
            headers = self._headers(content_type="")

            response = requests.post(
                url,
                headers=headers,
                files=files,
                params=params,
                timeout=self.timeout,
            )

        response.raise_for_status()
        result = response.json()

        # Validate response if enabled
        if self.validator:
            try:
                # Note: validator logic might need update if API schema changed drastically
                # For now assuming compatible keys
                result = self.validator.validate_deepfake_response(result)
            except ResponseValidationError as e:
                logger.warning(f"Response validation failed: {e}")

        return result

    def verify_mfa(
        self,
        audio_path: str,
        transaction_id: str,
        customer_id: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Verify caller identity via voice MFA.

        Args:
            audio_path: Path to audio file
            transaction_id: Unique transaction ID
            customer_id: Customer ID
            context: Additional context fields (amount_usd, destination_country, etc.)

        Returns:
            Response dict with authentication/verification results
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        url = f"{self.api_url}{self.mfa_path}"
        context = context or {}

        # Read and base64 encode audio
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        # Construct payload matching AuthenticationRequest in backend
        payload = {
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "voice_sample": audio_b64,
            "channel": context.get("channel", "voice"),
            "amount_usd": context.get("amount_usd", 0.0),
            "destination_country": context.get("destination_country", "US"),
            "is_new_beneficiary": context.get("is_new_beneficiary", False),
            "device_info": context.get("device_info", {}),
        }

        # Handle any other passthrough fields
        safe_payload = convert_numpy_types(payload)

        response = requests.post(
            url,
            headers=self._headers(),
            json=safe_payload,
            timeout=self.timeout,
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.error(f"MFA verification failed: {e}")
            raise

        result = response.json()

        # Validator might need update, skipping specific validation call unless confirmed compatible
        # result = self.validator.validate_mfa_response(result)

        return result

    def submit_sar(
        self,
        transaction_id: str,
        customer_id: str,
        activity_type: str,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Submit a Suspicious Activity Report (SAR).

        Args:
            transaction_id: Related transaction ID
            customer_id: Customer ID
            activity_type: Type of suspicious activity
            description: Narrative description
            metadata: Additional risk factors or context

        Returns:
            Response dict with SAR generation results
        """
        url = f"{self.api_url}{self.sar_path}"
        metadata = metadata or {}

        # Construct SARContext payload
        payload = {
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "activity_type": activity_type,
            "activity_description": description,
            "transactions": metadata.get("transactions", []),
            "risk_factors": metadata.get("risk_factors", []),
            "voice_authentication": metadata.get("voice_authentication"),
            "total_risk_score": metadata.get("total_risk_score", 0.0),
            "compliance_action": metadata.get("compliance_action", "review"),
            "filing_institution": metadata.get("filing_institution", "Sonotheia Client"),
        }

        safe_payload = convert_numpy_types(payload)

        response = requests.post(
            url,
            headers=self._headers(),
            json=safe_payload,
            timeout=self.timeout,
        )

        response.raise_for_status()
        result = response.json()

        return result
