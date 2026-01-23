"""Tests for webhook_receiver/app.py - FastAPI webhook receiver."""

from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import patch

import pytest

# Skip tests if webhook receiver not available
try:
    from fastapi.testclient import TestClient

    from webhook_receiver.app import (
        WebhookEvent,
        app,
        check_rate_limit,
        cleanup_old_data,
        verify_signature,
    )
except ImportError:
    pytestmark = pytest.mark.skip("webhook_receiver not available")


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def webhook_secret():
    """Test webhook secret."""
    return "test_secret_key_12345"


@pytest.fixture
def sample_event():
    """Sample webhook event data."""
    return {
        "type": "deepfake.completed",
        "id": "event-123",
        "event_id": "event-123",
        "data": {
            "session_id": "session-456",
            "score": 0.3,
            "label": "likely_real",
        },
        "timestamp": "2026-01-23T12:00:00Z",
    }


class TestVerifySignature:
    """Tests for verify_signature function."""

    def test_verify_signature_valid(self, webhook_secret):
        """Test valid signature verification."""
        payload = b'{"type":"test","data":{}}'
        signature = hmac.new(webhook_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

        assert verify_signature(payload, signature, webhook_secret) is True

    def test_verify_signature_invalid(self, webhook_secret):
        """Test invalid signature verification."""
        payload = b'{"type":"test","data":{}}'
        invalid_signature = "invalid_signature_12345"

        assert verify_signature(payload, invalid_signature, webhook_secret) is False

    def test_verify_signature_missing_secret(self):
        """Test signature verification without secret."""
        payload = b'{"type":"test","data":{}}'
        signature = "some_signature"

        assert verify_signature(payload, signature, None) is False

    def test_verify_signature_missing_signature(self, webhook_secret):
        """Test signature verification without signature header."""
        payload = b'{"type":"test","data":{}}'

        assert verify_signature(payload, None, webhook_secret) is False

    def test_verify_signature_invalid_format(self, webhook_secret):
        """Test signature verification with invalid format."""
        payload = b'{"type":"test","data":{}}'
        invalid_format = "not_64_chars"

        assert verify_signature(payload, invalid_format, webhook_secret) is False


class TestCheckRateLimit:
    """Tests for check_rate_limit function."""

    def test_rate_limit_within_limit(self):
        """Test rate limit check when within limit."""
        client_ip = "192.168.1.1"

        # First 100 requests should pass
        for _ in range(100):
            assert check_rate_limit(client_ip) is True

    def test_rate_limit_exceeded(self):
        """Test rate limit check when exceeded."""
        client_ip = "192.168.1.2"

        # Make 100 requests (at limit)
        for _ in range(100):
            check_rate_limit(client_ip)

        # 101st request should fail
        assert check_rate_limit(client_ip) is False

    def test_rate_limit_reset(self):
        """Test rate limit reset after window expires."""
        client_ip = "192.168.1.3"

        # Exhaust limit
        for _ in range(100):
            check_rate_limit(client_ip)

        # Simulate window expiration
        from webhook_receiver.app import rate_limit_store

        rate_limit_store[client_ip]["reset_time"] = 0  # Expired

        # Should reset and allow request
        assert check_rate_limit(client_ip) is True


class TestWebhookEndpoint:
    """Tests for /webhook endpoint."""

    def test_webhook_success(self, client, sample_event, webhook_secret):
        """Test successful webhook processing."""
        # Reset processed events
        from webhook_receiver.app import processed_events

        processed_events.clear()

        with patch("webhook_receiver.app.WEBHOOK_SECRET", webhook_secret):
            # Need to get raw body for signature
            payload = json.dumps(sample_event).encode()
            signature = hmac.new(
                webhook_secret.encode("utf-8"), payload, hashlib.sha256
            ).hexdigest()

            # Use content parameter to send raw bytes
            response = client.post(
                "/webhook",
                content=payload,
                headers={
                    "X-Sonotheia-Signature": signature,
                    "Content-Type": "application/json",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["received"] is True
            assert "event_id" in data

    def test_webhook_invalid_signature(self, client, sample_event, webhook_secret):
        """Test webhook with invalid signature."""
        with patch("webhook_receiver.app.WEBHOOK_SECRET", webhook_secret):
            response = client.post(
                "/webhook",
                json=sample_event,
                headers={"X-Sonotheia-Signature": "invalid_signature"},
            )

            assert response.status_code == 401

    def test_webhook_missing_signature(self, client, sample_event, webhook_secret):
        """Test webhook without signature header."""
        with patch("webhook_receiver.app.WEBHOOK_SECRET", webhook_secret):
            response = client.post("/webhook", json=sample_event)

            assert response.status_code == 401

    def test_webhook_idempotency(self, client, sample_event, webhook_secret):
        """Test webhook idempotency (duplicate events)."""
        # Reset processed events
        from webhook_receiver.app import processed_events

        processed_events.clear()

        with patch("webhook_receiver.app.WEBHOOK_SECRET", webhook_secret):
            payload = json.dumps(sample_event).encode()
            signature = hmac.new(
                webhook_secret.encode("utf-8"), payload, hashlib.sha256
            ).hexdigest()

            # First request
            response1 = client.post(
                "/webhook",
                content=payload,
                headers={
                    "X-Sonotheia-Signature": signature,
                    "Content-Type": "application/json",
                },
            )
            assert response1.status_code == 200
            assert response1.json()["received"] is True
            assert response1.json().get("duplicate") is not True

            # Duplicate request
            response2 = client.post(
                "/webhook",
                content=payload,
                headers={
                    "X-Sonotheia-Signature": signature,
                    "Content-Type": "application/json",
                },
            )
            assert response2.status_code == 200
            assert response2.json()["duplicate"] is True

    def test_webhook_rate_limiting(self, client, sample_event, webhook_secret):
        """Test webhook rate limiting."""
        with patch("webhook_receiver.app.WEBHOOK_SECRET", webhook_secret):
            payload = json.dumps(sample_event).encode()
            signature = hmac.new(
                webhook_secret.encode("utf-8"), payload, hashlib.sha256
            ).hexdigest()

            # Make many requests to trigger rate limit
            responses = []
            for i in range(105):  # Exceed limit of 100
                event = sample_event.copy()
                event["id"] = f"event-{i}"
                event["event_id"] = f"event-{i}"
                response = client.post(
                    "/webhook",
                    json=event,
                    headers={"X-Sonotheia-Signature": signature},
                )
                responses.append(response.status_code)

            # Should have some 429 responses
            assert 429 in responses

    def test_webhook_different_event_types(self, client, webhook_secret):
        """Test webhook with different event types."""
        with patch("webhook_receiver.app.WEBHOOK_SECRET", webhook_secret):
            # Reset processed events and rate limit between tests
            from webhook_receiver.app import processed_events, rate_limit_store

            processed_events.clear()
            rate_limit_store.clear()

            event_types = ["deepfake.completed", "mfa.completed", "sar.submitted"]

            for event_type in event_types:
                event = {
                    "type": event_type,
                    "id": f"event-{event_type}-{hash(event_type)}",
                    "data": {"session_id": f"test-session-{event_type}"},
                }
                payload = json.dumps(event).encode()
                signature = hmac.new(
                    webhook_secret.encode("utf-8"), payload, hashlib.sha256
                ).hexdigest()

                response = client.post(
                    "/webhook",
                    content=payload,
                    headers={
                        "X-Sonotheia-Signature": signature,
                        "Content-Type": "application/json",
                    },
                )

                assert response.status_code == 200


class TestCleanupOldData:
    """Tests for cleanup_old_data function."""

    def test_cleanup_expired_results(self):
        """Test cleanup of expired results."""
        from datetime import datetime, timedelta

        from webhook_receiver.app import results

        # Add an expired result
        old_time = (datetime.utcnow() - timedelta(days=2)).isoformat() + "Z"
        results["old_result"] = {
            "received_at": old_time,
            "data": {},
        }

        cleanup_old_data()

        assert "old_result" not in results

    def test_cleanup_enforces_max_results(self):
        """Test cleanup enforces maximum results limit."""
        from datetime import datetime

        from webhook_receiver.app import MAX_RESULTS, results

        # Clear existing results
        results.clear()

        # Add more than max results (using same format as app.py)
        for i in range(MAX_RESULTS + 10):
            results[f"result_{i}"] = {
                "received_at": datetime.utcnow().isoformat() + "Z",
                "data": {},
            }

        cleanup_old_data()

        assert len(results) <= MAX_RESULTS


class TestWebhookEventModel:
    """Tests for WebhookEvent Pydantic model."""

    def test_webhook_event_creation(self):
        """Test creating a WebhookEvent."""
        event = WebhookEvent(
            type="deepfake.completed",
            id="event-123",
            data={"session_id": "session-456"},
        )

        assert event.type == "deepfake.completed"
        assert event.id == "event-123"
        assert event.data["session_id"] == "session-456"

    def test_webhook_event_optional_fields(self):
        """Test WebhookEvent with optional fields."""
        event = WebhookEvent(
            type="mfa.completed",
            data={},
            timestamp="2026-01-23T12:00:00Z",
        )

        assert event.type == "mfa.completed"
        assert event.timestamp == "2026-01-23T12:00:00Z"
        assert event.id is None
