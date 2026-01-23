"""Tests for api_types.py - type definitions."""

from __future__ import annotations

import pytest

# Skip tests if api_types not available
try:
    from api_types import (
        AudioProperties,
        ClientConfig,
        DeepfakeMetadata,
        DeepfakeResponse,
        EnhancedClientConfig,
        ErrorResponse,
        MFAContext,
        MFAResponse,
        SARMetadata,
        SARResponse,
        ValidationErrorResponse,
        ValidationResultDict,
    )
except ImportError:
    pytestmark = pytest.mark.skip("api_types not available")


class TestTypeDefinitions:
    """Tests for type definition imports and structure."""

    def test_deepfake_response_structure(self):
        """Test DeepfakeResponse type structure."""
        response: DeepfakeResponse = {
            "score": 0.3,
            "label": "likely_real",
            "latency_ms": 450,
            "session_id": "session-123",
            "model_version": "1.0",
        }

        assert response["score"] == 0.3
        assert response["label"] == "likely_real"
        assert response["latency_ms"] == 450

    def test_mfa_response_structure(self):
        """Test MFAResponse type structure."""
        response: MFAResponse = {
            "verified": True,
            "enrollment_id": "enroll-123",
            "confidence": 0.85,
            "session_id": "session-456",
            "latency_ms": 320,
        }

        assert response["verified"] is True
        assert response["confidence"] == 0.85

    def test_sar_response_structure(self):
        """Test SARResponse type structure."""
        response: SARResponse = {
            "status": "submitted",
            "case_id": "case-789",
            "session_id": "session-123",
            "submitted_at": "2026-01-23T12:00:00Z",
        }

        assert response["status"] == "submitted"
        assert response["case_id"] == "case-789"

    def test_metadata_types(self):
        """Test metadata type definitions."""
        deepfake_meta: DeepfakeMetadata = {
            "session_id": "session-123",
            "channel": "web",
        }

        mfa_context: MFAContext = {
            "session_id": "session-456",
            "channel": "ivr",
            "ip_address": "192.168.1.1",
        }

        sar_meta: SARMetadata = {
            "source": "api",
            "analyst_id": "analyst-123",
        }

        assert deepfake_meta["session_id"] == "session-123"
        assert mfa_context["channel"] == "ivr"
        assert sar_meta["source"] == "api"

    def test_error_response_types(self):
        """Test error response type definitions."""
        error: ErrorResponse = {
            "error": "validation_error",
            "message": "Invalid request",
        }

        validation_error: ValidationErrorResponse = {
            "error": "validation_error",
            "message": "Invalid fields",
            "details": [
                {
                    "field": "audio",
                    "code": "required",
                    "message": "Audio file is required",
                }
            ],
        }

        assert error["error"] == "validation_error"
        assert len(validation_error["details"]) > 0

    def test_audio_properties_type(self):
        """Test AudioProperties type."""
        properties: AudioProperties = {
            "format": "wav",
            "codec": "pcm",
            "sample_rate": 16000,
            "channels": 1,
            "duration": 5.0,
            "bit_rate": 256000,
            "file_size": 160000,
        }

        assert properties["sample_rate"] == 16000
        assert properties["channels"] == 1

    def test_validation_result_dict_type(self):
        """Test ValidationResultDict type."""
        result: ValidationResultDict = {
            "is_valid": True,
            "file_path": "/path/to/audio.wav",
            "issues": [
                {
                    "level": "warning",
                    "message": "Low sample rate",
                    "field": "sample_rate",
                    "actual_value": 8000,
                    "expected_value": 16000,
                }
            ],
            "properties": {
                "format": "wav",
                "sample_rate": 8000,
            },
        }

        assert result["is_valid"] is True
        assert len(result["issues"]) > 0

    def test_client_config_types(self):
        """Test client configuration types."""
        config: ClientConfig = {
            "api_key": "test-key",
            "api_url": "https://api.test.com",
            "timeout": 30,
        }

        enhanced_config: EnhancedClientConfig = {
            "api_key": "test-key",
            "max_retries": 3,
            "rate_limit_rps": 2.0,
            "enable_circuit_breaker": True,
        }

        assert config["api_key"] == "test-key"
        assert enhanced_config["max_retries"] == 3
