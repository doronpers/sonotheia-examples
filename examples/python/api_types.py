"""
Type definitions for Sonotheia API requests and responses.

This module provides TypedDict definitions for better type safety and
IDE autocomplete when working with the Sonotheia API.

Usage:
    from api_types import DeepfakeResponse, MFAResponse, SARResponse

    def handle_deepfake(response: DeepfakeResponse) -> None:
        score = response["score"]  # IDE knows this is a float
        label = response["label"]  # IDE knows this is a str
"""

from __future__ import annotations

from typing import Literal, TypedDict


# Request types
class DeepfakeMetadata(TypedDict, total=False):
    """Metadata for deepfake detection requests."""

    session_id: str
    channel: str
    user_id: str
    request_id: str


class MFAContext(TypedDict, total=False):
    """Context for MFA verification requests."""

    session_id: str
    channel: str
    user_id: str
    ip_address: str
    device_id: str


class SARMetadata(TypedDict, total=False):
    """Metadata for SAR submission requests."""

    source: str
    analyst_id: str
    notes: str


# Response types
class DeepfakeResponse(TypedDict):
    """Response from deepfake detection endpoint."""

    score: float
    label: Literal["likely_synthetic", "likely_real", "uncertain"]
    latency_ms: int
    session_id: str
    model_version: str


class MFAResponse(TypedDict):
    """Response from MFA verification endpoint."""

    verified: bool
    enrollment_id: str
    confidence: float
    session_id: str
    latency_ms: int


class MFAResponseWithAction(MFAResponse):
    """MFA response with recommended action (when verification fails)."""

    recommended_action: Literal["deny", "defer_to_review"]


class SARResponse(TypedDict):
    """Response from SAR submission endpoint."""

    status: Literal["submitted", "pending", "processed"]
    case_id: str
    session_id: str
    submitted_at: str


class EnrollmentResponse(TypedDict):
    """Response from enrollment creation endpoint."""

    enrollment_id: str
    status: Literal["active", "pending", "completed"]
    samples_required: int
    samples_collected: int
    message: str


class HealthCheckResponse(TypedDict):
    """Response from health check endpoint."""

    status: Literal["healthy", "degraded", "unhealthy"]
    service: str
    version: str
    timestamp: str


# Error response types
class ErrorResponse(TypedDict):
    """Standard error response from API."""

    error: str
    message: str


class ValidationErrorDetail(TypedDict, total=False):
    """Detailed validation error information."""

    field: str
    code: str
    message: str


class ValidationErrorResponse(ErrorResponse):
    """Error response with validation details."""

    details: list[ValidationErrorDetail]


# Audio validation types
class AudioProperties(TypedDict, total=False):
    """Audio file properties."""

    format: str
    codec: str
    sample_rate: int
    channels: int
    duration: float
    bit_rate: int
    file_size: int


class ValidationIssueDict(TypedDict):
    """Dictionary representation of a validation issue."""

    level: Literal["error", "warning", "info"]
    message: str
    field: str | None
    actual_value: float | int | str | None
    expected_value: float | int | str | list[str] | None


class ValidationResultDict(TypedDict):
    """Dictionary representation of validation result."""

    is_valid: bool
    file_path: str
    issues: list[ValidationIssueDict]
    properties: AudioProperties


# Configuration types
class ClientConfig(TypedDict, total=False):
    """Configuration for API client."""

    api_key: str
    api_url: str
    deepfake_path: str
    mfa_path: str
    sar_path: str
    timeout: int


class EnhancedClientConfig(ClientConfig, total=False):
    """Configuration for enhanced API client with additional features."""

    max_retries: int
    rate_limit_rps: float
    enable_circuit_breaker: bool


# Mock server types
class MockConfig(TypedDict, total=False):
    """Configuration for mock API server."""

    deepfake_latency_ms: int
    mfa_latency_ms: int
    sar_latency_ms: int
    rate_limit_per_minute: int
    always_succeed: bool
    simulate_errors: bool
    error_rate: float
    default_deepfake_score: float
    default_mfa_confidence: float


class MockStats(TypedDict):
    """Statistics from mock API server."""

    total_sessions: int
    total_enrollments: int
    total_sar_cases: int
    request_counts: dict[str, int]
