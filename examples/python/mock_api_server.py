"""
Mock Sonotheia API server for integration testing.

This mock server implements the core Sonotheia API endpoints for testing purposes,
allowing developers to test their integrations without using real API credentials
or consuming API quota.

Features:
- Deepfake detection endpoint
- MFA verification endpoint
- SAR submission endpoint
- Webhook simulation
- Configurable responses
- Request validation
- Rate limiting simulation

Usage:
    # Start the mock server
    python mock_api_server.py

    # Use in tests
    export SONOTHEIA_API_URL=http://localhost:8000
    python main.py audio.wav

    # Start with custom port
    python mock_api_server.py --port 9000
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from typing import Any, Callable

from flask import Flask, Response, jsonify, request

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class MockConfig:
    """Configuration for mock server behavior."""

    # Authentication
    api_key: str = "mock_api_key_12345"
    webhook_secret: str = "mock_webhook_secret"

    # Simulated processing time
    deepfake_latency_ms: int = 500
    mfa_latency_ms: int = 400
    sar_latency_ms: int = 200

    # Rate limiting
    rate_limit_per_minute: int = 100

    # Response behavior
    always_succeed: bool = False
    simulate_errors: bool = True
    error_rate: float = 0.05  # 5% error rate

    # Default scores
    default_deepfake_score: float = 0.5
    default_mfa_confidence: float = 0.85


@dataclass
class MockStorage:
    """Centralized storage for mock data."""

    enrollments: dict[str, Any] = field(default_factory=dict)
    sessions: dict[str, Any] = field(default_factory=dict)
    sar_cases: dict[str, Any] = field(default_factory=dict)
    request_count: dict[str, int] = field(default_factory=dict)

    def clear(self) -> None:
        """Clear all stored data."""
        self.enrollments.clear()
        self.sessions.clear()
        self.sar_cases.clear()
        self.request_count.clear()


# Global instances
config = MockConfig()
storage = MockStorage()

# Create Flask app
app = Flask(__name__)


def verify_api_key() -> tuple[bool, str | None]:
    """Verify API key from request headers."""
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return False, "Missing or invalid Authorization header"

    api_key = auth_header.replace("Bearer ", "")

    if api_key != config.api_key:
        return False, "Invalid API key"

    return True, None


def check_rate_limit(client_id: str) -> tuple[bool, dict[str, str]]:
    """Check if request should be rate limited."""
    now = time.time()
    minute = int(now / 60)
    key = f"{client_id}:{minute}"

    count = storage.request_count.get(key, 0)

    headers = {
        "X-RateLimit-Limit": str(config.rate_limit_per_minute),
        "X-RateLimit-Remaining": str(max(0, config.rate_limit_per_minute - count - 1)),
        "X-RateLimit-Reset": str((minute + 1) * 60),
    }

    if count >= config.rate_limit_per_minute:
        return False, headers

    storage.request_count[key] = count + 1
    return True, headers


def require_auth_and_rate_limit(f: Callable) -> Callable:
    """Decorator to check authentication and rate limits."""

    @wraps(f)
    def decorated_function(*args, **kwargs) -> tuple[Response, int] | Response:
        # Verify API key
        valid, error = verify_api_key()
        if not valid:
            return jsonify({"error": "Unauthorized", "message": error}), 401

        # Check rate limit
        client_id = request.headers.get("X-Client-ID", "default")
        rate_ok, rate_headers = check_rate_limit(client_id)

        if not rate_ok:
            response = jsonify(
                {
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please retry later",
                }
            )
            response.headers.update(rate_headers)
            return response, 429

        # Store rate headers for the response
        kwargs["rate_headers"] = rate_headers
        return f(*args, **kwargs)

    return decorated_function


def simulate_processing_delay(latency_ms: int):
    """Simulate API processing time."""
    time.sleep(latency_ms / 1000.0)


def should_simulate_error() -> tuple[bool, tuple[int, dict[str, Any]] | None]:
    """Determine if an error should be simulated."""
    if config.always_succeed or not config.simulate_errors:
        return False, None

    if random.random() < config.error_rate:
        errors = [
            (500, {"error": "Internal server error", "message": "Simulated error"}),
            (
                503,
                {
                    "error": "Service unavailable",
                    "message": "Service temporarily unavailable",
                },
            ),
            (400, {"error": "Bad request", "message": "Invalid audio format"}),
        ]
        status_code, error_body = random.choice(errors)
        return True, (status_code, error_body)

    return False, None


@app.route("/v1/voice/deepfake", methods=["POST"])
@app.route("/api/detect", methods=["POST"])
@require_auth_and_rate_limit
def deepfake_detect(rate_headers: dict[str, str] | None = None):
    """Mock deepfake detection endpoint."""
    # Validate request
    if "audio" in request.files:
        audio_file = request.files["audio"]
    elif "file" in request.files:
        audio_file = request.files["file"]
    else:
        return (
            jsonify({"error": "Bad request", "message": "Missing 'audio' or 'file' in request"}),
            400,
        )

    # Validate file is not empty
    audio_file.seek(0, 2)  # Seek to end
    file_size = audio_file.tell()
    audio_file.seek(0)  # Reset to beginning

    if file_size == 0:
        return jsonify({"error": "Bad request", "message": "Audio file is empty"}), 400

    # Check for simulated errors
    has_error, error_response = should_simulate_error()
    if has_error and error_response:
        status_code, error_body = error_response
        return jsonify(error_body), status_code

    # Parse metadata
    metadata = {}
    if "metadata" in request.form:
        try:
            metadata = json.loads(request.form["metadata"])
        except json.JSONDecodeError:
            pass

    # Simulate processing
    simulate_processing_delay(config.deepfake_latency_ms)

    # Generate mock response
    session_id = metadata.get("session_id", f"session-{uuid.uuid4().hex[:12]}")

    # Generate a score based on filename or random
    filename = audio_file.filename or "unknown.wav"
    score, label = _generate_deepfake_score(filename)

    # Store session
    storage.sessions[session_id] = {
        "score": score,
        "label": label,
        "timestamp": datetime.utcnow().isoformat(),
        "filename": filename,
        "metadata": metadata,
    }

    response_data = {
        "score": round(score, 3),
        "label": label,
        "latency_ms": config.deepfake_latency_ms,
        "session_id": session_id,
        "model_version": "mock-v1.0",
    }

    response = jsonify(response_data)
    if rate_headers:
        response.headers.update(rate_headers)

    logger.info(f"Deepfake detection: score={score:.3f}, label={label}, session={session_id}")

    return response


def _generate_deepfake_score(filename: str) -> tuple[float, str]:
    """Generate deepfake score and label based on filename.

    Args:
        filename: Name of the audio file

    Returns:
        Tuple of (score, label)
    """
    if "synthetic" in filename.lower() or "fake" in filename.lower():
        return random.uniform(0.7, 0.95), "likely_synthetic"
    elif "real" in filename.lower() or "authentic" in filename.lower():
        return random.uniform(0.05, 0.35), "likely_real"
    else:
        return random.uniform(0.3, 0.7), "uncertain"


@app.route("/v1/mfa/voice/verify", methods=["POST"])
@app.route("/api/authenticate", methods=["POST"])
@require_auth_and_rate_limit
def mfa_verify(rate_headers: dict[str, str] | None = None):
    """Mock MFA verification endpoint."""
    # Validate request
    # Handle JSON request (used by client.py)
    if request.is_json:
        data = request.get_json()
        audio_b64 = data.get("voice_sample")
        if not audio_b64:
            return jsonify({"error": "Bad request", "message": "Missing 'voice_sample'"}), 400

        # In JSON mode (client.py), enrollment_id is not mapped directly in standard payload?
        # client.py sends: transaction_id, customer_id.
        # But golden_path_demo sends enrollment_id as customer_id?
        # Let's check client.py verify_mfa args.
        # client.verify_mfa(audio_path, enrollment_id, context=...) -> maps enrollment_id to params?
        # wrapper: verify_mfa(audio_path, transaction_id, customer_id)
        # golden_path: verify_mfa(..., enrollment_id, context={...})
        # Wait, golden_path calls verify_mfa with enrollment_id as 2nd arg (transaction_id).

        # So transaction_id = enrollment_id in this demo usage.
        enrollment_id = data.get("customer_id") or data.get("transaction_id")

        filename = "unknown.wav"  # Filename not available in base64 payload

    # Handle Multipart request (legacy/other clients)
    elif "audio" in request.files or "file" in request.files:
        if "audio" in request.files:
            audio_file = request.files["audio"]
        else:
            audio_file = request.files["file"]

        enrollment_id = request.form.get("enrollment_id")
        filename = audio_file.filename or "unknown.wav"
    else:
        return (
            jsonify({"error": "Bad request", "message": "Missing audio/file or JSON body"}),
            400,
        )

    if not enrollment_id:
        return (jsonify({"error": "Bad request", "message": "Missing enrollment identifier"}), 400)

    # Check for simulated errors
    has_error, error_response = should_simulate_error()
    if has_error and error_response:
        status_code, error_body = error_response
        return jsonify(error_body), status_code

    # Check if enrollment exists (create it if not for testing)
    if enrollment_id not in storage.enrollments:
        logger.info(f"Creating mock enrollment: {enrollment_id}")
        storage.enrollments[enrollment_id] = {
            "created_at": datetime.utcnow().isoformat(),
            "samples": 3,
        }

    # Parse context
    context = {}
    if request.is_json:
        # Context might be scattered in fields
        context = request.get_json()
    elif "context" in request.form:
        try:
            context = json.loads(request.form["context"])
        except json.JSONDecodeError:
            pass

    # Simulate processing
    simulate_processing_delay(config.mfa_latency_ms)

    # Generate mock response
    session_id = context.get("session_id", f"session-{uuid.uuid4().hex[:12]}")

    # Generate confidence score
    confidence, verified = _generate_mfa_score(filename)

    response_data = {
        "verified": verified,
        "enrollment_id": enrollment_id,
        "confidence": round(confidence, 3),
        "session_id": session_id,
        "latency_ms": config.mfa_latency_ms,
    }

    if not verified:
        response_data["recommended_action"] = "defer_to_review" if confidence > 0.30 else "deny"

    response = jsonify(response_data)
    if rate_headers:
        response.headers.update(rate_headers)

    logger.info(
        f"MFA verification: verified={verified}, "
        f"confidence={confidence:.3f}, enrollment={enrollment_id}"
    )

    return response


def _generate_mfa_score(filename: str) -> tuple[float, bool]:
    """Generate MFA confidence score and verification result based on filename.

    Args:
        filename: Name of the audio file

    Returns:
        Tuple of (confidence, verified)
    """
    if "mismatch" in filename.lower() or "invalid" in filename.lower():
        confidence = random.uniform(0.15, 0.45)
        return confidence, False
    elif "match" in filename.lower() or "valid" in filename.lower():
        confidence = random.uniform(0.85, 0.98)
        return confidence, True
    else:
        confidence = random.uniform(0.50, 0.90)
        return confidence, confidence >= 0.70


@app.route("/v1/reports/sar", methods=["POST"])
@app.route("/api/sar/generate", methods=["POST"])
@require_auth_and_rate_limit
def sar_submit(rate_headers: dict[str, str] | None = None):
    """Mock SAR submission endpoint."""
    # Parse JSON body
    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Bad request", "message": "Invalid JSON body"}), 400

    # Validate required fields
    session_id = data.get("session_id")
    decision = data.get("decision")
    reason = data.get("reason")

    if not all([session_id, decision, reason]):
        return (
            jsonify(
                {
                    "error": "Bad request",
                    "message": "Missing required fields: session_id, decision, reason",
                }
            ),
            400,
        )

    if decision not in ["allow", "deny", "review"]:
        return (
            jsonify(
                {
                    "error": "Bad request",
                    "message": "Invalid decision. Must be 'allow', 'deny', or 'review'",
                }
            ),
            400,
        )

    # Check for simulated errors
    has_error, error_response = should_simulate_error()
    if has_error and error_response:
        status_code, error_body = error_response
        return jsonify(error_body), status_code

    # Simulate processing
    simulate_processing_delay(config.sar_latency_ms)

    # Generate mock response
    case_id = f"sar-{uuid.uuid4().hex[:12]}"
    submission_time = datetime.utcnow().isoformat()

    # Store SAR case
    storage.sar_cases[case_id] = {
        "session_id": session_id,
        "decision": decision,
        "reason": reason,
        "metadata": data.get("metadata", {}),
        "submitted_at": submission_time,
    }

    response_data = {
        "status": "submitted",
        "case_id": case_id,
        "session_id": session_id,
        "submitted_at": submission_time,
    }

    response = jsonify(response_data)
    if rate_headers:
        response.headers.update(rate_headers)

    logger.info(f"SAR submitted: case_id={case_id}, decision={decision}, session={session_id}")

    return response


@app.route("/v1/enrollment", methods=["POST"])
@require_auth_and_rate_limit
def enrollment_create(rate_headers: dict[str, str] | None = None):
    """Mock enrollment creation endpoint."""
    # Validate request
    if "audio" not in request.files and "file" not in request.files:
        return (
            jsonify(
                {"error": "Bad request", "message": "Missing 'audio' or 'file' in request"}
            ),
            400,
        )

    # Parse metadata
    metadata = {}
    if "metadata" in request.form:
        try:
            metadata = json.loads(request.form["metadata"])
        except json.JSONDecodeError:
            pass

    # Generate enrollment ID
    enrollment_id = f"enroll-{uuid.uuid4().hex[:12]}"

    # Store enrollment
    storage.enrollments[enrollment_id] = {
        "enrollment_id": enrollment_id,
        "created_at": datetime.utcnow().isoformat(),
        "samples": 1,
        "metadata": metadata,
    }

    response_data = {
        "enrollment_id": enrollment_id,
        "status": "active",
        "samples_required": 3,
        "samples_collected": 1,
        "message": "Enrollment created successfully. Submit 2 more samples to complete.",
    }

    logger.info(f"Enrollment created: {enrollment_id}")

    response = jsonify(response_data)
    if rate_headers:
        response.headers.update(rate_headers)

    return response, 201


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "service": "mock-sonotheia-api",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@app.route("/mock/config", methods=["GET", "POST"])
def mock_config_endpoint():
    """Configure mock server behavior."""
    if request.method == "GET":
        return jsonify(
            {
                "deepfake_latency_ms": config.deepfake_latency_ms,
                "mfa_latency_ms": config.mfa_latency_ms,
                "sar_latency_ms": config.sar_latency_ms,
                "rate_limit_per_minute": config.rate_limit_per_minute,
                "always_succeed": config.always_succeed,
                "simulate_errors": config.simulate_errors,
                "error_rate": config.error_rate,
            }
        )

    # Update configuration
    data = request.get_json()

    for key, value in data.items():
        if hasattr(config, key):
            setattr(config, key, value)
            logger.info(f"Updated config: {key} = {value}")

    return jsonify({"status": "updated", "config": data})


@app.route("/mock/stats", methods=["GET"])
def mock_stats():
    """Get mock server statistics."""
    return jsonify(
        {
            "total_sessions": len(storage.sessions),
            "total_enrollments": len(storage.enrollments),
            "total_sar_cases": len(storage.sar_cases),
            "request_counts": dict(storage.request_count),
        }
    )


@app.route("/mock/reset", methods=["POST"])
def mock_reset():
    """Reset mock server state."""
    storage.clear()
    logger.info("Mock server state reset")
    return jsonify({"status": "reset"})


def main():
    """Start the mock API server."""
    parser = argparse.ArgumentParser(description="Mock Sonotheia API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument(
        "--api-key", default=None, help="Mock API key (default: mock_api_key_12345)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Update mock API key if provided
    if args.api_key:
        config.api_key = args.api_key

    logger.info("=" * 60)
    logger.info("Mock Sonotheia API Server")
    logger.info("=" * 60)
    logger.info(f"Host: {args.host}:{args.port}")
    logger.info(f"Mock API Key: {config.api_key}")
    logger.info(f"API URL: http://{args.host}:{args.port}")
    logger.info("")
    logger.info("Endpoints:")
    logger.info("  POST /v1/voice/deepfake       - Deepfake detection")
    logger.info("  POST /v1/mfa/voice/verify     - MFA verification")
    logger.info("  POST /v1/reports/sar          - SAR submission")
    logger.info("  POST /v1/enrollment           - Create enrollment")
    logger.info("  GET  /health                  - Health check")
    logger.info("  GET  /mock/config             - Get configuration")
    logger.info("  POST /mock/config             - Update configuration")
    logger.info("  GET  /mock/stats              - Get statistics")
    logger.info("  POST /mock/reset              - Reset state")
    logger.info("")
    logger.info("Usage:")
    logger.info(f"  export SONOTHEIA_API_URL=http://localhost:{args.port}")
    logger.info(f"  export SONOTHEIA_API_KEY={config.api_key}")
    logger.info("  python main.py audio.wav")
    logger.info("=" * 60)
    logger.info("Registered Routes:")
    logger.info(app.url_map)

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
