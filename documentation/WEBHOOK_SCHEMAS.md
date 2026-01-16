# Webhook Payload Schemas

This document provides detailed schemas for all webhook events sent by the Sonotheia API.

## Overview

Webhooks allow you to receive real-time notifications when asynchronous operations complete. The Sonotheia API sends HTTP POST requests to your registered webhook URL with event data.

## Webhook Security

### Signature Verification

All webhook requests include an `X-Sonotheia-Signature` header containing an HMAC-SHA256 signature:

```
X-Sonotheia-Signature: sha256=abc123def456...
```

**Verification Process:**

```python
import hmac
import hashlib

def verify_webhook_signature(payload_body, signature_header, webhook_secret):
    """Verify webhook signature"""
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        payload_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Extract signature from header (format: "sha256=...")
    if signature_header.startswith('sha256='):
        received_signature = signature_header[7:]
    else:
        received_signature = signature_header

    return hmac.compare_digest(expected_signature, received_signature)

# Usage in webhook handler
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    payload = request.data.decode('utf-8')
    signature = request.headers.get('X-Sonotheia-Signature')

    if not verify_webhook_signature(payload, signature, WEBHOOK_SECRET):
        return 'Invalid signature', 401

    # Process webhook...
```

### Additional Security Measures

- **HTTPS Only**: Webhook URLs must use HTTPS
- **IP Allowlist**: Optionally restrict to Sonotheia IP ranges
- **Secret Rotation**: Periodically rotate webhook secrets
- **Idempotency**: Handle duplicate events using event IDs

## Common Webhook Headers

All webhook requests include these headers:

```http
POST /your-webhook-endpoint HTTP/1.1
Host: your-domain.com
Content-Type: application/json
X-Sonotheia-Signature: sha256=abc123def456...
X-Sonotheia-Event: deepfake.completed
X-Sonotheia-Event-Id: evt_7gH3jK9mN2pQ4rS
X-Sonotheia-Timestamp: 2026-01-05T12:34:56.789Z
X-Sonotheia-Delivery-Id: dlv_aB1cD2eF3gH4
User-Agent: Sonotheia-Webhook/1.0
```

## Base Event Structure

All webhook events follow this structure:

```typescript
interface WebhookEvent {
  event_id: string;           // Unique event identifier
  event_type: string;         // Event type (e.g., "deepfake.completed")
  timestamp: string;          // ISO 8601 timestamp
  api_version: string;        // API version (e.g., "v1")
  data: object;               // Event-specific payload
  metadata?: object;          // Optional metadata from original request
}
```

## Event Types

### 1. Deepfake Detection Events

#### `deepfake.completed`

Fired when asynchronous deepfake detection completes.

**Payload Schema:**

```json
{
  "event_id": "evt_7gH3jK9mN2pQ4rS",
  "event_type": "deepfake.completed",
  "timestamp": "2026-01-05T12:34:56.789Z",
  "api_version": "v1",
  "data": {
    "session_id": "sess_abc123def456",
    "score": 0.82,
    "label": "likely_synthetic",
    "confidence": 0.87,
    "recommended_action": "defer_to_review",
    "latency_ms": 640,
    "audio_metadata": {
      "duration_seconds": 8.5,
      "sample_rate": 16000,
      "channels": 1,
      "format": "wav"
    },
    "analysis": {
      "temporal_consistency": 0.79,
      "spectral_artifacts": 0.85,
      "prosody_naturalness": 0.71
    }
  },
  "metadata": {
    "request_id": "req_xyz789",
    "submitted_at": "2026-01-05T12:34:50.123Z"
  }
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Unique session identifier |
| `score` | number | Deepfake probability (0.0-1.0) |
| `label` | string | Classification label (see Label Values below) |
| `confidence` | number | Model confidence (0.0-1.0) |
| `recommended_action` | string | Suggested action: `accept`, `deny`, `defer_to_review` |
| `latency_ms` | number | Processing time in milliseconds |
| `audio_metadata` | object | Audio file characteristics |
| `analysis` | object | Detailed analysis scores |

**Label Values:**
- `likely_real`: High confidence the audio is genuine
- `likely_synthetic`: High confidence the audio is deepfake
- `uncertain`: Model is uncertain, defer to review

#### `deepfake.failed`

Fired when deepfake detection fails.

```json
{
  "event_id": "evt_9kL5mN7oP3qR6sT",
  "event_type": "deepfake.failed",
  "timestamp": "2026-01-05T12:35:00.123Z",
  "api_version": "v1",
  "data": {
    "session_id": "sess_failed123",
    "error": {
      "code": "AUDIO_TOO_SHORT",
      "message": "Audio duration must be at least 3 seconds",
      "details": {
        "duration_seconds": 1.2,
        "minimum_required": 3.0
      }
    }
  },
  "metadata": {
    "request_id": "req_failed456"
  }
}
```

### 2. Voice MFA Events

#### `mfa.completed`

Fired when voice verification completes.

**Payload Schema:**

```json
{
  "event_id": "evt_2bC4dE6fG8hJ0k",
  "event_type": "mfa.completed",
  "timestamp": "2026-01-05T12:36:15.456Z",
  "api_version": "v1",
  "data": {
    "session_id": "sess_mfa789xyz",
    "verified": true,
    "enrollment_id": "enroll_abc123def456",
    "user_id": "user_12345",
    "confidence": 0.93,
    "similarity_score": 0.91,
    "liveness_score": 0.88,
    "latency_ms": 520,
    "audio_metadata": {
      "duration_seconds": 6.2,
      "sample_rate": 16000,
      "channels": 1,
      "format": "wav"
    },
    "biometric_data": {
      "voice_quality": 0.89,
      "background_noise": 0.12,
      "speaking_rate": "normal"
    }
  },
  "metadata": {
    "request_id": "req_mfa456",
    "submitted_at": "2026-01-05T12:36:14.900Z",
    "context": {
      "ip_address": "192.0.2.1",
      "device_id": "dev_mobile123"
    }
  }
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `verified` | boolean | Whether voice matched enrollment |
| `enrollment_id` | string | Reference to voice enrollment |
| `user_id` | string | User identifier |
| `confidence` | number | Overall verification confidence (0.0-1.0) |
| `similarity_score` | number | Voice similarity to enrollment (0.0-1.0) |
| `liveness_score` | number | Liveness detection score (0.0-1.0) |
| `biometric_data` | object | Additional biometric metrics |

#### `mfa.failed`

Fired when voice verification fails.

```json
{
  "event_id": "evt_3cD5eF7gH9iK1l",
  "event_type": "mfa.failed",
  "timestamp": "2026-01-05T12:37:00.789Z",
  "api_version": "v1",
  "data": {
    "session_id": "sess_mfa_fail123",
    "verified": false,
    "enrollment_id": "enroll_abc123def456",
    "user_id": "user_12345",
    "reason": "INSUFFICIENT_SIMILARITY",
    "confidence": 0.42,
    "similarity_score": 0.38,
    "error": {
      "code": "VERIFICATION_FAILED",
      "message": "Voice does not match enrollment profile",
      "details": {
        "threshold": 0.75,
        "actual_score": 0.38
      }
    }
  }
}
```

#### `mfa.enrollment.completed`

Fired when voice enrollment completes.

```json
{
  "event_id": "evt_4dE6fG8hI0jL2m",
  "event_type": "mfa.enrollment.completed",
  "timestamp": "2026-01-05T12:38:30.234Z",
  "api_version": "v1",
  "data": {
    "enrollment_id": "enroll_new789xyz",
    "user_id": "user_67890",
    "status": "active",
    "quality_score": 0.94,
    "samples_processed": 3,
    "created_at": "2026-01-05T12:38:30.234Z",
    "voice_characteristics": {
      "pitch_range": "medium",
      "speaking_rate": "normal",
      "accent": "en-US"
    }
  },
  "metadata": {
    "request_id": "req_enroll789",
    "device": "mobile_app"
  }
}
```

### 3. SAR (Suspicious Activity Report) Events

#### `sar.submitted`

Fired when SAR submission is processed.

**Payload Schema:**

```json
{
  "event_id": "evt_5eF7gH9iJ1kM3n",
  "event_type": "sar.submitted",
  "timestamp": "2026-01-05T12:40:45.567Z",
  "api_version": "v1",
  "data": {
    "case_id": "sar-001234",
    "session_id": "sess_abc123def456",
    "status": "submitted",
    "decision": "deny",
    "reason": "Suspected synthetic voice detected",
    "submitted_at": "2026-01-05T12:40:45.567Z",
    "evidence": {
      "deepfake_score": 0.82,
      "mfa_verified": false,
      "risk_level": "high"
    },
    "compliance": {
      "regulation": "BSA/AML",
      "jurisdiction": "US",
      "retention_period_days": 2555
    }
  },
  "metadata": {
    "request_id": "req_sar456",
    "analyst_id": "analyst_789",
    "review_notes": "Manual review recommended"
  }
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `case_id` | string | Unique SAR case identifier |
| `session_id` | string | Related session ID |
| `status` | string | SAR status: `submitted`, `pending`, `filed` |
| `decision` | string | Action taken: `allow`, `deny`, `review` |
| `reason` | string | Human-readable reason |
| `evidence` | object | Supporting evidence |
| `compliance` | object | Compliance metadata |

#### `sar.filed`

Fired when SAR is officially filed with authorities.

```json
{
  "event_id": "evt_6fG8hI0jK2lN4o",
  "event_type": "sar.filed",
  "timestamp": "2026-01-05T14:00:00.000Z",
  "api_version": "v1",
  "data": {
    "case_id": "sar-001234",
    "filing_reference": "BSA-E-20260105-001234",
    "filed_at": "2026-01-05T14:00:00.000Z",
    "authority": "FinCEN",
    "status": "filed"
  }
}
```

### 4. System Events

#### `system.health_check`

Periodic health check event (if enabled).

```json
{
  "event_id": "evt_7gH9iJ1kL3mO5p",
  "event_type": "system.health_check",
  "timestamp": "2026-01-05T12:00:00.000Z",
  "api_version": "v1",
  "data": {
    "status": "healthy",
    "services": {
      "deepfake": "operational",
      "mfa": "operational",
      "sar": "operational"
    },
    "response_times_ms": {
      "deepfake": 640,
      "mfa": 520
    }
  }
}
```

## Webhook Response Requirements

Your webhook endpoint must:

1. **Respond quickly**: Return 2xx status code within 5 seconds
2. **Process asynchronously**: Queue long-running tasks
3. **Return appropriate status codes**:
   - `200 OK`: Event processed successfully
   - `201 Created`: Event processed and resource created
   - `202 Accepted`: Event queued for processing
   - `400 Bad Request`: Invalid payload
   - `401 Unauthorized`: Invalid signature
   - `500 Server Error`: Processing failed (will retry)

## Retry Policy

If webhook delivery fails, Sonotheia retries with exponential backoff:

- **Attempt 1**: Immediate
- **Attempt 2**: After 5 seconds
- **Attempt 3**: After 25 seconds
- **Attempt 4**: After 125 seconds (2 minutes)
- **Attempt 5**: After 625 seconds (10 minutes)
- **Final**: After 3125 seconds (52 minutes)

**Total retry window**: ~1 hour

After all retries fail, the event is marked as undelivered and can be retrieved via the API.

## Idempotency

Use `event_id` to detect and handle duplicate deliveries:

```python
processed_events = set()  # Or use database

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    event = request.json
    event_id = event['event_id']

    # Check if already processed
    if event_id in processed_events:
        return 'Already processed', 200

    # Process event
    process_event(event)

    # Mark as processed
    processed_events.add(event_id)

    return 'Success', 200
```

## Complete Example: Webhook Server

```python
from flask import Flask, request, jsonify
import hmac
import hashlib
import os

app = Flask(__name__)
WEBHOOK_SECRET = os.getenv('SONOTHEIA_WEBHOOK_SECRET')

def verify_signature(payload_body, signature_header):
    """Verify HMAC-SHA256 signature"""
    expected = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        payload_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    received = signature_header.replace('sha256=', '')
    return hmac.compare_digest(expected, received)

@app.route('/webhook/sonotheia', methods=['POST'])
def handle_webhook():
    # Get raw payload for signature verification
    payload = request.data.decode('utf-8')
    signature = request.headers.get('X-Sonotheia-Signature')

    # Verify signature
    if not verify_signature(payload, signature):
        return jsonify({'error': 'Invalid signature'}), 401

    # Parse event
    event = request.json
    event_type = event['event_type']
    event_id = event['event_id']

    # Handle different event types
    if event_type == 'deepfake.completed':
        handle_deepfake_completed(event['data'])
    elif event_type == 'mfa.completed':
        handle_mfa_completed(event['data'])
    elif event_type == 'sar.submitted':
        handle_sar_submitted(event['data'])
    else:
        print(f"Unknown event type: {event_type}")

    return jsonify({'status': 'success', 'event_id': event_id}), 200

def handle_deepfake_completed(data):
    session_id = data['session_id']
    score = data['score']
    action = data['recommended_action']

    print(f"Deepfake detection completed for {session_id}")
    print(f"Score: {score}, Action: {action}")

    # Update your database, send notifications, etc.

def handle_mfa_completed(data):
    verified = data['verified']
    user_id = data['user_id']
    confidence = data['confidence']

    print(f"MFA verification for {user_id}: {verified} (confidence: {confidence})")

    # Update session, grant/deny access, etc.

def handle_sar_submitted(data):
    case_id = data['case_id']
    decision = data['decision']

    print(f"SAR submitted: {case_id}, Decision: {decision}")

    # Log to compliance system, notify analysts, etc.

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
```

## Testing Webhooks

### Local Testing with ngrok

```bash
# Start ngrok tunnel
ngrok http 3000

# Use ngrok URL as webhook endpoint
# https://abc123.ngrok.io/webhook/sonotheia

# Start your webhook server
python webhook_server.py
```

### Manual Testing

```bash
# Simulate webhook event
curl -X POST http://localhost:3000/webhook/sonotheia \
  -H "Content-Type: application/json" \
  -H "X-Sonotheia-Signature: sha256=$(echo -n '{"event_id":"test","event_type":"deepfake.completed"}' | openssl dgst -sha256 -hmac 'your_secret' | cut -d' ' -f2)" \
  -H "X-Sonotheia-Event: deepfake.completed" \
  -d '{"event_id":"test","event_type":"deepfake.completed","timestamp":"2026-01-05T12:00:00Z","api_version":"v1","data":{"session_id":"test","score":0.5,"label":"uncertain"}}'
```

## Webhook Management API

### Register Webhook

```bash
POST /v1/webhooks
Content-Type: application/json

{
  "url": "https://your-domain.com/webhook/sonotheia",
  "events": ["deepfake.completed", "mfa.completed", "sar.submitted"],
  "secret": "your_webhook_secret"
}
```

### List Webhooks

```bash
GET /v1/webhooks
```

### Delete Webhook

```bash
DELETE /v1/webhooks/{webhook_id}
```

### Retrieve Failed Events

```bash
GET /v1/webhooks/events?status=failed&since=2026-01-05T00:00:00Z
```

## Related Documentation

- [Webhook Server Example](../examples/node/webhook-server.js)
- [Best Practices Guide](BEST_PRACTICES.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Enhanced Examples](ENHANCED_EXAMPLES.md)
