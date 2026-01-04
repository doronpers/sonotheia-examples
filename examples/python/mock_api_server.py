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
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from flask import Flask, jsonify, request

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Mock configuration
MOCK_API_KEY = "mock_api_key_12345"
MOCK_WEBHOOK_SECRET = "mock_webhook_secret"

# In-memory storage
enrollments = {}
sessions = {}
sar_cases = {}
request_count = {}


@dataclass
class MockConfig:
    """Configuration for mock server behavior."""

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


config = MockConfig()


def verify_api_key():
    """Verify API key from request headers."""
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return False, "Missing or invalid Authorization header"

    api_key = auth_header.replace("Bearer ", "")

    if api_key != MOCK_API_KEY:
        return False, "Invalid API key"

    return True, None


def check_rate_limit(client_id: str) -> tuple[bool, dict[str, Any]]:
    """Check if request should be rate limited."""
    now = time.time()
    minute = int(now / 60)
    key = f"{client_id}:{minute}"

    count = request_count.get(key, 0)

    headers = {
        "X-RateLimit-Limit": str(config.rate_limit_per_minute),
        "X-RateLimit-Remaining": str(max(0, config.rate_limit_per_minute - count - 1)),
        "X-RateLimit-Reset": str((minute + 1) * 60),
    }

    if count >= config.rate_limit_per_minute:
        return False, headers

    request_count[key] = count + 1
    return True, headers


def simulate_processing_delay(latency_ms: int):
    """Simulate API processing time."""
    time.sleep(latency_ms / 1000.0)


def should_simulate_error() -> tuple[bool, dict[str, Any] | None]:
    """Determine if an error should be simulated."""
    if config.always_succeed or not config.simulate_errors:
        return False, None

    if random.random() < config.error_rate:
        errors = [
            (500, {"error": "Internal server error", "message": "Simulated error"}),
            (503, {"error": "Service unavailable", "message": "Service temporarily unavailable"}),
            (400, {"error": "Bad request", "message": "Invalid audio format"}),
        ]
        status_code, error_body = random.choice(errors)
        return True, (status_code, error_body)

    return False, None


@app.route("/v1/voice/deepfake", methods=["POST"])
def deepfake_detect():
    """Mock deepfake detection endpoint."""
    # Verify API key
    valid, error = verify_api_key()
    if not valid:
        return jsonify({"error": "Unauthorized", "message": error}), 401

    # Check rate limit
    client_id = request.headers.get("X-Client-ID", "default")
    rate_ok, rate_headers = check_rate_limit(client_id)

    if not rate_ok:
        response = jsonify(
            {"error": "Rate limit exceeded", "message": "Too many requests. Please retry later"}
        )
        response.headers.update(rate_headers)
        return response, 429

    # Validate request
    if "audio" not in request.files:
        return jsonify({"error": "Bad request", "message": "Missing 'audio' file in request"}), 400

    audio_file = request.files["audio"]

    # Validate file is not empty
    audio_file.seek(0, 2)  # Seek to end
    file_size = audio_file.tell()
    audio_file.seek(0)  # Reset to beginning

    if file_size == 0:
        return jsonify({"error": "Bad request", "message": "Audio file is empty"}), 400

    # Check for simulated errors
    has_error, error_response = should_simulate_error()
    if has_error:
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
    if "synthetic" in filename.lower() or "fake" in filename.lower():
        score = random.uniform(0.7, 0.95)
        label = "likely_synthetic"
    elif "real" in filename.lower() or "authentic" in filename.lower():
        score = random.uniform(0.05, 0.35)
        label = "likely_real"
    else:
        score = random.uniform(0.3, 0.7)
        label = "uncertain"

    # Store session
    sessions[session_id] = {
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
    response.headers.update(rate_headers)

    logger.info(f"Deepfake detection: score={score:.3f}, label={label}, session={session_id}")

    return response


@app.route("/v1/mfa/voice/verify", methods=["POST"])
def mfa_verify():
    """Mock MFA verification endpoint."""
    # Verify API key
    valid, error = verify_api_key()
    if not valid:
        return jsonify({"error": "Unauthorized", "message": error}), 401

    # Check rate limit
    client_id = request.headers.get("X-Client-ID", "default")
    rate_ok, rate_headers = check_rate_limit(client_id)

    if not rate_ok:
        response = jsonify(
            {"error": "Rate limit exceeded", "message": "Too many requests. Please retry later"}
        )
        response.headers.update(rate_headers)
        return response, 429

    # Validate request
    if "audio" not in request.files:
        return jsonify({"error": "Bad request", "message": "Missing 'audio' file in request"}), 400

    enrollment_id = request.form.get("enrollment_id")
    if not enrollment_id:
        return jsonify(
            {"error": "Bad request", "message": "Missing 'enrollment_id' in request"}
        ), 400

    audio_file = request.files["audio"]

    # Check for simulated errors
    has_error, error_response = should_simulate_error()
    if has_error:
        status_code, error_body = error_response
        return jsonify(error_body), status_code

    # Check if enrollment exists (create it if not for testing)
    if enrollment_id not in enrollments:
        logger.info(f"Creating mock enrollment: {enrollment_id}")
        enrollments[enrollment_id] = {"created_at": datetime.utcnow().isoformat(), "samples": 3}

    # Parse context
    context = {}
    if "context" in request.form:
        try:
            context = json.loads(request.form["context"])
        except json.JSONDecodeError:
            pass

    # Simulate processing
    simulate_processing_delay(config.mfa_latency_ms)

    # Generate mock response
    session_id = context.get("session_id", f"session-{uuid.uuid4().hex[:12]}")

    # Generate confidence score
    filename = audio_file.filename or "unknown.wav"
    if "match" in filename.lower() or "valid" in filename.lower():
        confidence = random.uniform(0.85, 0.98)
        verified = True
    elif "mismatch" in filename.lower() or "invalid" in filename.lower():
        confidence = random.uniform(0.15, 0.45)
        verified = False
    else:
        confidence = random.uniform(0.50, 0.90)
        verified = confidence >= 0.70

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
    response.headers.update(rate_headers)

    logger.info(
        f"MFA verification: verified={verified}, confidence={confidence:.3f}, enrollment={enrollment_id}"
    )

    return response


@app.route("/v1/reports/sar", methods=["POST"])
def sar_submit():
    """Mock SAR submission endpoint."""
    # Verify API key
    valid, error = verify_api_key()
    if not valid:
        return jsonify({"error": "Unauthorized", "message": error}), 401

    # Check rate limit
    client_id = request.headers.get("X-Client-ID", "default")
    rate_ok, rate_headers = check_rate_limit(client_id)

    if not rate_ok:
        response = jsonify(
            {"error": "Rate limit exceeded", "message": "Too many requests. Please retry later"}
        )
        response.headers.update(rate_headers)
        return response, 429

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
        return jsonify(
            {
                "error": "Bad request",
                "message": "Missing required fields: session_id, decision, reason",
            }
        ), 400

    if decision not in ["allow", "deny", "review"]:
        return jsonify(
            {
                "error": "Bad request",
                "message": "Invalid decision. Must be 'allow', 'deny', or 'review'",
            }
        ), 400

    # Check for simulated errors
    has_error, error_response = should_simulate_error()
    if has_error:
        status_code, error_body = error_response
        return jsonify(error_body), status_code

    # Simulate processing
    simulate_processing_delay(config.sar_latency_ms)

    # Generate mock response
    case_id = f"sar-{uuid.uuid4().hex[:12]}"

    # Store SAR case
    sar_cases[case_id] = {
        "session_id": session_id,
        "decision": decision,
        "reason": reason,
        "metadata": data.get("metadata", {}),
        "submitted_at": datetime.utcnow().isoformat(),
    }

    response_data = {
        "status": "submitted",
        "case_id": case_id,
        "session_id": session_id,
        "submitted_at": datetime.utcnow().isoformat(),
    }

    response = jsonify(response_data)
    response.headers.update(rate_headers)

    logger.info(f"SAR submitted: case_id={case_id}, decision={decision}, session={session_id}")

    return response


@app.route("/v1/enrollment", methods=["POST"])
def enrollment_create():
    """Mock enrollment creation endpoint."""
    # Verify API key
    valid, error = verify_api_key()
    if not valid:
        return jsonify({"error": "Unauthorized", "message": error}), 401

    # Validate request
    if "audio" not in request.files:
        return jsonify({"error": "Bad request", "message": "Missing 'audio' file in request"}), 400

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
    enrollments[enrollment_id] = {
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

    return jsonify(response_data), 201


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
            "total_sessions": len(sessions),
            "total_enrollments": len(enrollments),
            "total_sar_cases": len(sar_cases),
            "request_counts": dict(request_count),
        }
    )


@app.route("/mock/reset", methods=["POST"])
def mock_reset():
    """Reset mock server state."""
    sessions.clear()
    enrollments.clear()
    sar_cases.clear()
    request_count.clear()

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
        global MOCK_API_KEY
        MOCK_API_KEY = args.api_key

    logger.info("=" * 60)
    logger.info("Mock Sonotheia API Server")
    logger.info("=" * 60)
    logger.info(f"Host: {args.host}:{args.port}")
    logger.info(f"Mock API Key: {MOCK_API_KEY}")
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
    logger.info(f"  export SONOTHEIA_API_KEY={MOCK_API_KEY}")
    logger.info("  python main.py audio.wav")
    logger.info("=" * 60)

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
