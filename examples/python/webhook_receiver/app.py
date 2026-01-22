"""
FastAPI webhook receiver for Sonotheia API callbacks.

This demonstrates how to:
- Receive asynchronous processing results
- Verify webhook signatures
- Handle different event types
- Implement idempotency
- Apply rate limiting
- Store results for later retrieval

Usage:
    # Start webhook server
    python app.py

    # Or with uvicorn
    uvicorn app:app --host 0.0.0.0 --port 8080 --reload
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Sonotheia Webhook Receiver",
    description="Example webhook receiver for Sonotheia API callbacks",
    version="1.0.0",
)

# Configuration
WEBHOOK_SECRET = os.getenv("SONOTHEIA_WEBHOOK_SECRET")
PORT = int(os.getenv("PORT", "8080"))
MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE_MB", "10")) * 1024 * 1024  # 10MB default

# In-memory stores (use a database in production)
results: dict[str, dict[str, Any]] = {}
processed_events: set[str] = set()
rate_limit_store: dict[str, dict[str, Any]] = defaultdict(dict)

# Rate limiting configuration
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 100
MAX_EVENT_ID_CACHE = 50000

# TTL configuration
RESULT_TTL_SECONDS = 24 * 60 * 60  # 24 hours
MAX_RESULTS = 10000


class WebhookEvent(BaseModel):
    """Webhook event payload model."""

    type: str
    id: str | None = None
    event_id: str | None = None
    data: dict[str, Any]
    timestamp: str | None = None


def verify_signature(payload: bytes, signature: str | None, secret: str | None) -> bool:
    """
    Verify webhook signature using HMAC-SHA256.

    Args:
        payload: Raw request body bytes
        signature: Signature from X-Sonotheia-Signature header
        secret: Webhook secret from environment

    Returns:
        True if signature is valid, False otherwise
    """
    if not secret:
        logger.error("WEBHOOK_SECRET not set - webhook verification required")
        return False

    if not signature:
        logger.warn("Missing signature header")
        return False

    # Validate signature format (64 hex characters for SHA-256)
    if not isinstance(signature, str) or not all(c in "0123456789abcdefABCDEF" for c in signature):
        logger.warn(
            f"Invalid signature format - expected 64 hex characters, got: {signature[:20]}..."
        )
        return False

    if len(signature) != 64:
        logger.warn(f"Invalid signature length - expected 64, got {len(signature)}")
        return False

    try:
        expected_signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False


def check_rate_limit(client_ip: str) -> bool:
    """
    Check if client has exceeded rate limit.

    Args:
        client_ip: Client IP address

    Returns:
        True if within limit, False if exceeded
    """
    now = time.time()
    entry = rate_limit_store[client_ip]

    # Reset if window expired
    if not entry.get("reset_time") or now > entry["reset_time"]:
        entry["count"] = 0
        entry["reset_time"] = now + RATE_LIMIT_WINDOW_SECONDS

    # Check limit
    if entry["count"] >= RATE_LIMIT_MAX_REQUESTS:
        logger.warn(f"Rate limit exceeded for {client_ip}: {entry['count']} requests")
        return False

    # Increment counter
    entry["count"] += 1
    return True


def cleanup_old_data():
    """Clean up old results and processed event IDs."""
    now = datetime.utcnow()

    # Clean up old results
    expired_keys = [
        key
        for key, value in results.items()
        if (
            now - datetime.fromisoformat(value["received_at"].replace("Z", "+00:00"))
        ).total_seconds()
        > RESULT_TTL_SECONDS
    ]
    for key in expired_keys:
        del results[key]

    if expired_keys:
        logger.info(f"Cleaned up {len(expired_keys)} expired results")

    # Enforce max results limit
    if len(results) > MAX_RESULTS:
        to_delete = len(results) - MAX_RESULTS
        keys_to_delete = list(results.keys())[:to_delete]
        for key in keys_to_delete:
            del results[key]
        logger.warn(f"Enforced max results limit: deleted {to_delete} entries")

    # Clean up processed event IDs if cache is too large
    if len(processed_events) > MAX_EVENT_ID_CACHE:
        to_delete = len(processed_events) - MAX_EVENT_ID_CACHE
        event_ids = list(processed_events)[:to_delete]
        for event_id in event_ids:
            processed_events.discard(event_id)
        logger.info(f"Cleaned up {to_delete} processed event IDs")

    # Clean up rate limit store
    expired_ips = [
        ip for ip, entry in rate_limit_store.items() if entry.get("reset_time", 0) < now.timestamp()
    ]
    for ip in expired_ips:
        del rate_limit_store[ip]


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    client_ip = request.client.host if request.client else "unknown"

    if request.url.path == "/webhook":
        if not check_rate_limit(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {RATE_LIMIT_MAX_REQUESTS} requests per minute",
                },
            )

    response = await call_next(request)
    return response


# Header dependency for webhook signature (module-level to avoid B008 warning)
_webhook_signature_header = Header(None, alias="X-Sonotheia-Signature")


@app.post("/webhook")
async def webhook_endpoint(
    event: WebhookEvent,
    request: Request,
    x_sonotheia_signature: str | None = _webhook_signature_header,
):
    """
    Main webhook endpoint for receiving Sonotheia API callbacks.

    Features:
    - Signature verification
    - Idempotency (duplicate events ignored)
    - Rate limiting
    - Event routing
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify signature if secret is configured
    if WEBHOOK_SECRET:
        if not x_sonotheia_signature or not verify_signature(
            body, x_sonotheia_signature, WEBHOOK_SECRET
        ):
            logger.warn("Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature"
            )

    # Idempotency check: ignore duplicate events
    event_id = (
        event.id or event.event_id or f"{event.type}-{event.data.get('session_id', 'unknown')}"
    )
    if event_id in processed_events:
        logger.info(f"Duplicate event ignored (idempotency): {event_id}")
        return {"received": True, "duplicate": True, "event_id": event_id}

    logger.debug(f"Webhook received: type={event.type}, id={event_id}")

    try:
        # Route to appropriate handler
        if event.type == "deepfake.completed":
            session_id = event.data.get("session_id", "unknown")
            results[session_id] = {
                "type": "deepfake",
                "score": event.data.get("score"),
                "label": event.data.get("label"),
                "timestamp": event.data.get("timestamp"),
                "received_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            }
            logger.info(f"Deepfake event processed: session_id={session_id}")

        elif event.type == "mfa.completed":
            session_id = event.data.get("session_id", "unknown")
            results[session_id] = {
                "type": "mfa",
                "enrollment_id": event.data.get("enrollment_id"),
                "verified": event.data.get("verified"),
                "confidence": event.data.get("confidence"),
                "received_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            }
            logger.info(f"MFA event processed: session_id={session_id}")

        elif event.type == "sar.submitted":
            session_id = event.data.get("session_id", "unknown")
            results[session_id] = {
                "type": "sar",
                "case_id": event.data.get("case_id"),
                "status": event.data.get("status"),
                "received_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            }
            logger.info(f"SAR event processed: session_id={session_id}")

        else:
            logger.warn(f"Unknown event type: {event.type}")

        # Mark event as processed
        processed_events.add(event_id)

        return {"received": True, "event_id": event_id}

    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    cleanup_old_data()  # Run cleanup on health check
    return {
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "results_count": len(results),
        "processed_events_count": len(processed_events),
    }


@app.get("/results/{session_id}")
async def get_result(session_id: str):
    """Retrieve result by session ID."""
    if session_id not in results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return results[session_id]


@app.get("/results")
async def list_results():
    """List all stored results."""
    cleanup_old_data()
    return {
        "count": len(results),
        "results": [{"session_id": session_id, **data} for session_id, data in results.items()],
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("Webhook receiver starting up")
    logger.info(f"Port: {PORT}")
    logger.info(
        f"Rate limit: {RATE_LIMIT_MAX_REQUESTS} requests per {RATE_LIMIT_WINDOW_SECONDS} seconds"
    )
    logger.info(f"Max request size: {MAX_REQUEST_SIZE / 1024 / 1024:.1f}MB")
    logger.info(f"Idempotency: Enabled (tracks up to {MAX_EVENT_ID_CACHE} event IDs)")

    if not WEBHOOK_SECRET:
        logger.warning("SONOTHEIA_WEBHOOK_SECRET not set - signature verification disabled")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Webhook receiver shutting down")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
