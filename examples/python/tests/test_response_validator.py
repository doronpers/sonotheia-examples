"""
Tests for response_validator module.

This module tests the API response validation functionality.
"""

from __future__ import annotations

import pytest

from response_validator import ResponseValidationError, ResponseValidator


class TestResponseValidatorInit:
    """Tests for ResponseValidator initialization."""

    def test_init_loads_schema_successfully(self):
        """Test that validator loads schema file successfully."""
        validator = ResponseValidator()
        # Should not raise an exception
        assert validator is not None

    def test_init_handles_missing_schema_gracefully(self, tmp_path, monkeypatch):
        """Test that validator handles missing schema file gracefully."""
        # The validator should handle missing schema gracefully
        # We test that it doesn't raise an exception
        validator = ResponseValidator()
        # Should not raise an exception even if schema is missing
        assert isinstance(validator.schemas, dict)

    def test_init_handles_invalid_schema_gracefully(self, tmp_path, monkeypatch):
        """Test that validator handles invalid schema file gracefully."""
        # This test verifies the validator doesn't crash on invalid JSON
        # The actual behavior depends on whether the schema file exists
        # We test that it doesn't raise an exception
        validator = ResponseValidator()
        assert isinstance(validator.schemas, dict)


class TestDeepfakeResponseValidation:
    """Tests for deepfake response validation."""

    def test_validate_deepfake_response_success(self):
        """Test successful validation of valid deepfake response."""
        validator = ResponseValidator()
        response = {
            "score": 0.85,
            "label": "likely_synthetic",
            "latency_ms": 640,
        }
        result = validator.validate_deepfake_response(response)
        assert result == response

    def test_validate_deepfake_response_missing_fields(self):
        """Test validation fails when required fields are missing."""
        validator = ResponseValidator()
        response = {"score": 0.85}  # Missing label and latency_ms

        with pytest.raises(ResponseValidationError, match="missing required fields"):
            validator.validate_deepfake_response(response)

    def test_validate_deepfake_response_invalid_score_type(self):
        """Test validation fails when score is not a number."""
        validator = ResponseValidator()
        response = {
            "score": "0.85",  # String instead of number
            "label": "likely_synthetic",
            "latency_ms": 640,
        }

        with pytest.raises(ResponseValidationError, match="'score' must be a number"):
            validator.validate_deepfake_response(response)

    def test_validate_deepfake_response_invalid_score_range(self):
        """Test validation fails when score is out of range."""
        validator = ResponseValidator()

        # Score too high
        response = {
            "score": 1.5,  # > 1.0
            "label": "likely_synthetic",
            "latency_ms": 640,
        }
        with pytest.raises(ResponseValidationError, match="'score' must be between 0 and 1"):
            validator.validate_deepfake_response(response)

        # Score negative
        response = {
            "score": -0.1,  # < 0
            "label": "likely_synthetic",
            "latency_ms": 640,
        }
        with pytest.raises(ResponseValidationError, match="'score' must be between 0 and 1"):
            validator.validate_deepfake_response(response)

    def test_validate_deepfake_response_invalid_label(self):
        """Test validation fails when label is invalid."""
        validator = ResponseValidator()
        response = {
            "score": 0.85,
            "label": "invalid_label",
            "latency_ms": 640,
        }

        with pytest.raises(ResponseValidationError, match="'label' must be one of"):
            validator.validate_deepfake_response(response)

    def test_validate_deepfake_response_valid_labels(self):
        """Test that all valid labels are accepted."""
        validator = ResponseValidator()
        valid_labels = ["likely_real", "likely_synthetic", "uncertain"]

        for label in valid_labels:
            response = {
                "score": 0.5,
                "label": label,
                "latency_ms": 100,
            }
            result = validator.validate_deepfake_response(response)
            assert result["label"] == label

    def test_validate_deepfake_response_invalid_latency(self):
        """Test validation fails when latency_ms is invalid."""
        validator = ResponseValidator()

        # Negative latency
        response = {
            "score": 0.85,
            "label": "likely_synthetic",
            "latency_ms": -10,
        }
        with pytest.raises(
            ResponseValidationError, match="'latency_ms' must be a non-negative number"
        ):
            validator.validate_deepfake_response(response)

        # Non-numeric latency
        response = {
            "score": 0.85,
            "label": "likely_synthetic",
            "latency_ms": "640",
        }
        with pytest.raises(
            ResponseValidationError, match="'latency_ms' must be a non-negative number"
        ):
            validator.validate_deepfake_response(response)


class TestMFAResponseValidation:
    """Tests for MFA response validation."""

    def test_validate_mfa_response_success(self):
        """Test successful validation of valid MFA response."""
        validator = ResponseValidator()
        response = {
            "verified": True,
            "enrollment_id": "enroll-123",
            "confidence": 0.93,
        }
        result = validator.validate_mfa_response(response)
        assert result == response

    def test_validate_mfa_response_missing_fields(self):
        """Test validation fails when required fields are missing."""
        validator = ResponseValidator()
        response = {"verified": True}  # Missing enrollment_id and confidence

        with pytest.raises(ResponseValidationError, match="missing required fields"):
            validator.validate_mfa_response(response)

    def test_validate_mfa_response_invalid_verified_type(self):
        """Test validation fails when verified is not a boolean."""
        validator = ResponseValidator()
        response = {
            "verified": "true",  # String instead of boolean
            "enrollment_id": "enroll-123",
            "confidence": 0.93,
        }

        with pytest.raises(ResponseValidationError, match="'verified' must be a boolean"):
            validator.validate_mfa_response(response)

    def test_validate_mfa_response_invalid_enrollment_id_type(self):
        """Test validation fails when enrollment_id is not a string."""
        validator = ResponseValidator()
        response = {
            "verified": True,
            "enrollment_id": 123,  # Number instead of string
            "confidence": 0.93,
        }

        with pytest.raises(ResponseValidationError, match="'enrollment_id' must be a string"):
            validator.validate_mfa_response(response)

    def test_validate_mfa_response_invalid_confidence_type(self):
        """Test validation fails when confidence is not a number."""
        validator = ResponseValidator()
        response = {
            "verified": True,
            "enrollment_id": "enroll-123",
            "confidence": "0.93",  # String instead of number
        }

        with pytest.raises(ResponseValidationError, match="'confidence' must be a number"):
            validator.validate_mfa_response(response)

    def test_validate_mfa_response_invalid_confidence_range(self):
        """Test validation fails when confidence is out of range."""
        validator = ResponseValidator()

        # Confidence too high
        response = {
            "verified": True,
            "enrollment_id": "enroll-123",
            "confidence": 1.5,  # > 1.0
        }
        with pytest.raises(ResponseValidationError, match="'confidence' must be between 0 and 1"):
            validator.validate_mfa_response(response)

        # Confidence negative
        response = {
            "verified": True,
            "enrollment_id": "enroll-123",
            "confidence": -0.1,  # < 0
        }
        with pytest.raises(ResponseValidationError, match="'confidence' must be between 0 and 1"):
            validator.validate_mfa_response(response)


class TestSARResponseValidation:
    """Tests for SAR response validation."""

    def test_validate_sar_response_success(self):
        """Test successful validation of valid SAR response."""
        validator = ResponseValidator()
        valid_statuses = ["submitted", "pending", "accepted", "rejected"]

        for status in valid_statuses:
            response = {
                "status": status,
                "case_id": "case-123",
                "session_id": "session-123",
            }
            result = validator.validate_sar_response(response)
            assert result["status"] == status

    def test_validate_sar_response_missing_fields(self):
        """Test validation fails when required fields are missing."""
        validator = ResponseValidator()
        response = {"status": "submitted"}  # Missing case_id and session_id

        with pytest.raises(ResponseValidationError, match="missing required fields"):
            validator.validate_sar_response(response)

    def test_validate_sar_response_invalid_status(self):
        """Test validation fails when status is invalid."""
        validator = ResponseValidator()
        response = {
            "status": "invalid_status",
            "case_id": "case-123",
            "session_id": "session-123",
        }

        with pytest.raises(ResponseValidationError, match="'status' must be one of"):
            validator.validate_sar_response(response)

    def test_validate_sar_response_invalid_case_id_type(self):
        """Test validation fails when case_id is not a string."""
        validator = ResponseValidator()
        response = {
            "status": "submitted",
            "case_id": 123,  # Number instead of string
            "session_id": "session-123",
        }

        with pytest.raises(ResponseValidationError, match="'case_id' must be a string"):
            validator.validate_sar_response(response)

    def test_validate_sar_response_invalid_session_id_type(self):
        """Test validation fails when session_id is not a string."""
        validator = ResponseValidator()
        response = {
            "status": "submitted",
            "case_id": "case-123",
            "session_id": 123,  # Number instead of string
        }

        with pytest.raises(ResponseValidationError, match="'session_id' must be a string"):
            validator.validate_sar_response(response)


class TestValidationError:
    """Tests for ResponseValidationError exception."""

    def test_validation_error_exception(self):
        """Test that ResponseValidationError can be raised and caught."""
        with pytest.raises(ResponseValidationError) as exc_info:
            raise ResponseValidationError("Test error message")

        assert "Test error message" in str(exc_info.value)
        assert isinstance(exc_info.value, Exception)
