"""
API response validation module for Sonotheia API.

This module provides validation functions to ensure API responses
match expected schemas and contain all required fields.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ResponseValidationError(Exception):
    """Raised when API response doesn't match expected schema."""

    pass


class ResponseValidator:
    """Validates Sonotheia API responses against expected schemas."""

    def __init__(self):
        """Initialize validator with schema definitions."""
        # Find schema file - try multiple locations
        module_dir = Path(__file__).parent

        # Try relative to module (for installed package)
        schema_path = module_dir.parent.parent / "schemas" / "api-responses.json"

        # Try relative to repository root (for development)
        if not schema_path.exists():
            # When running from examples/python, go up to repo root
            repo_root = module_dir.parent.parent
            schema_path = repo_root / "schemas" / "api-responses.json"

        if not schema_path.exists():
            # Fallback: disable validation if schema not found
            logger.warning("Schema file not found, validation disabled")
            self.schemas = {}
            return

        try:
            with open(schema_path) as f:
                schemas = json.load(f)
                self.schemas = schemas.get("definitions", {})
        except Exception as e:
            logger.warning(f"Failed to load schema file: {e}, validation disabled")
            self.schemas = {}

    def validate_deepfake_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """
        Validate deepfake detection response.

        Args:
            response: API response dictionary

        Returns:
            Validated response dictionary

        Raises:
            ResponseValidationError: If response doesn't match schema
        """
        required_fields = ["score", "label", "latency_ms"]
        self._check_required_fields(response, required_fields, "deepfake")

        # Validate field types and values
        if not isinstance(response["score"], (int, float)):
            raise ResponseValidationError("'score' must be a number")

        if not 0 <= response["score"] <= 1:
            raise ResponseValidationError("'score' must be between 0 and 1")

        valid_labels = ["likely_real", "likely_synthetic", "uncertain"]
        if response["label"] not in valid_labels:
            raise ResponseValidationError(
                f"'label' must be one of {valid_labels}, got '{response['label']}'"
            )

        if not isinstance(response["latency_ms"], (int, float)) or response["latency_ms"] < 0:
            raise ResponseValidationError("'latency_ms' must be a non-negative number")

        logger.debug(
            f"Validated deepfake response: score={response['score']}, label={response['label']}"
        )
        return response

    def validate_mfa_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """
        Validate MFA verification response.

        Args:
            response: API response dictionary

        Returns:
            Validated response dictionary

        Raises:
            ResponseValidationError: If response doesn't match schema
        """
        required_fields = ["verified", "enrollment_id", "confidence"]
        self._check_required_fields(response, required_fields, "MFA")

        # Validate field types and values
        if not isinstance(response["verified"], bool):
            raise ResponseValidationError("'verified' must be a boolean")

        if not isinstance(response["enrollment_id"], str):
            raise ResponseValidationError("'enrollment_id' must be a string")

        if not isinstance(response["confidence"], (int, float)):
            raise ResponseValidationError("'confidence' must be a number")

        if not 0 <= response["confidence"] <= 1:
            raise ResponseValidationError("'confidence' must be between 0 and 1")

        logger.debug(
            f"Validated MFA response: verified={response['verified']}, "
            f"confidence={response['confidence']}"
        )
        return response

    def validate_sar_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """
        Validate SAR submission response.

        Args:
            response: API response dictionary

        Returns:
            Validated response dictionary

        Raises:
            ResponseValidationError: If response doesn't match schema
        """
        required_fields = ["status", "case_id", "session_id"]
        self._check_required_fields(response, required_fields, "SAR")

        # Validate field types and values
        valid_statuses = ["submitted", "pending", "accepted", "rejected"]
        if response["status"] not in valid_statuses:
            raise ResponseValidationError(
                f"'status' must be one of {valid_statuses}, got '{response['status']}'"
            )

        if not isinstance(response["case_id"], str):
            raise ResponseValidationError("'case_id' must be a string")

        if not isinstance(response["session_id"], str):
            raise ResponseValidationError("'session_id' must be a string")

        logger.debug(
            f"Validated SAR response: status={response['status']}, case_id={response['case_id']}"
        )
        return response

    def _check_required_fields(
        self, response: dict[str, Any], required_fields: list[str], response_type: str
    ) -> None:
        """Check that all required fields are present in response."""
        missing_fields = [field for field in required_fields if field not in response]

        if missing_fields:
            raise ResponseValidationError(
                f"{response_type} response missing required fields: {', '.join(missing_fields)}"
            )
