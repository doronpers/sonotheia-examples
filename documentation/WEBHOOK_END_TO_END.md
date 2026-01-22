# Webhook Integration End-to-End Guide

Complete guide for setting up and testing webhook integration with Sonotheia API.

## Overview

Webhooks allow you to receive asynchronous notifications when Sonotheia completes processing. This is useful for:
- Long-running analysis tasks
- Batch processing workflows
- Event-driven architectures
- Reducing API polling overhead

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Sonotheia │         │   Your       │         │  Your       │
│     API     │────────▶│  Webhook     │────────▶│ Application │
│             │  POST   │  Receiver    │  Store  │             │
└─────────────┘         └──────────────┘         └─────────────┘
```

## Step 1: Set Up Webhook Receiver

### Option A: Python (FastAPI)

```bash
cd examples/python/webhook_receiver
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set webhook secret
export SONOTHEIA_WEBHOOK_SECRET=your_secret_here

# Start server
python app.py
# Server runs on http://localhost:8080
```

### Option B: Node.js (Express)

```bash
cd examples/node
npm install

# Set webhook secret
export SONOTHEIA_WEBHOOK_SECRET=your_secret_here

# Start server
npm run webhook
# Server runs on http://localhost:3000
```

## Step 2: Configure Webhook URL

### For Testing (Local Development)

Use a tunneling service to expose your local server:

```bash
# Using ngrok
ngrok http 8080

# Or using localtunnel
npx localtunnel --port 8080
```

### For Production

1. Deploy webhook receiver to your infrastructure
2. Configure HTTPS (required for production)
3. Register webhook URL with Sonotheia (contact your integration engineer)

## Step 3: Webhook Event Types

### Deepfake Detection Completed

```json
{
  "type": "deepfake.completed",
  "id": "event-abc123",
  "data": {
    "session_id": "session-xyz789",
    "score": 0.82,
    "label": "likely_synthetic",
    "latency_ms": 640,
    "timestamp": "2026-01-21T12:00:00Z"
  }
}
```

### MFA Verification Completed

```json
{
  "type": "mfa.completed",
  "id": "event-def456",
  "data": {
    "session_id": "session-xyz789",
    "enrollment_id": "enroll-123",
    "verified": true,
    "confidence": 0.93,
    "timestamp": "2026-01-21T12:00:05Z"
  }
}
```

### SAR Submitted

```json
{
  "type": "sar.submitted",
  "id": "event-ghi789",
  "data": {
    "session_id": "session-xyz789",
    "case_id": "sar-001234",
    "status": "submitted",
    "timestamp": "2026-01-21T12:00:10Z"
  }
}
```

## Step 4: Signature Verification

All webhooks include an `X-Sonotheia-Signature` header for verification:

```python
import hmac
import hashlib

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

**Security Best Practices:**
- Always verify signatures in production
- Use constant-time comparison (`hmac.compare_digest`)
- Store webhook secret securely (environment variables, secrets manager)
- Never log the secret

## Step 5: Idempotency

Webhooks may be delivered multiple times. Implement idempotency:

```python
processed_events = set()

def handle_webhook(event):
    event_id = event.get('id') or event.get('event_id')
    
    if event_id in processed_events:
        logger.info(f"Duplicate event ignored: {event_id}")
        return
    
    # Process event
    process_event(event)
    
    # Mark as processed
    processed_events.add(event_id)
```

## Step 6: Rate Limiting

Protect your webhook endpoint from abuse:

```python
from collections import defaultdict
import time

rate_limit_store = defaultdict(dict)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 100  # requests per window

def check_rate_limit(client_ip: str) -> bool:
    now = time.time()
    entry = rate_limit_store[client_ip]
    
    if now > entry.get('reset_time', 0):
        entry['count'] = 0
        entry['reset_time'] = now + RATE_LIMIT_WINDOW
    
    if entry['count'] >= RATE_LIMIT_MAX:
        return False
    
    entry['count'] += 1
    return True
```

## Step 7: Error Handling

Implement robust error handling:

```python
@app.post("/webhook")
async def webhook_endpoint(event: WebhookEvent):
    try:
        # Verify signature
        if not verify_signature(...):
            return {"error": "Invalid signature"}, 401
        
        # Process event
        process_event(event)
        
        return {"received": True}
        
    except ValueError as e:
        logger.error(f"Invalid event: {e}")
        return {"error": "Invalid event"}, 400
        
    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        # Return 200 to prevent retries for processing errors
        # Or return 5xx if you want API to retry
        return {"error": "Processing failed"}, 500
```

## Step 8: Testing

### Test with Mock Server

```bash
# Terminal 1: Start mock API server
cd examples/python
python mock_api_server.py

# Terminal 2: Start webhook receiver
cd webhook_receiver
python app.py

# Terminal 3: Send test webhook
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -H "X-Sonotheia-Signature: test_signature" \
  -d '{
    "type": "deepfake.completed",
    "id": "test-123",
    "data": {
      "session_id": "test-session",
      "score": 0.5,
      "label": "uncertain"
    }
  }'
```

### Test with Golden Path Demo

The golden path demo can be configured to send webhooks (when API supports it):

```bash
python golden_path_demo.py audio.wav \
  --webhook-url http://localhost:8080/webhook
```

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Kubernetes

See `examples/kubernetes/deployment.yaml` for a complete Kubernetes deployment example.

### Security Checklist

- [ ] HTTPS enabled (TLS 1.2+)
- [ ] Signature verification enabled
- [ ] Rate limiting configured
- [ ] Request size limits set
- [ ] Idempotency implemented
- [ ] Error handling robust
- [ ] Logging configured (no secrets in logs)
- [ ] Monitoring/alerting set up
- [ ] Database for result storage (not in-memory)
- [ ] Backup/disaster recovery plan

## Troubleshooting

### Webhook Not Received

1. **Check receiver is running**: `curl http://localhost:8080/health`
2. **Verify URL is accessible**: Test from external network
3. **Check firewall rules**: Ensure port is open
4. **Verify webhook registration**: Confirm URL is registered with Sonotheia

### Invalid Signature Errors

1. **Check secret matches**: Verify `SONOTHEIA_WEBHOOK_SECRET` is correct
2. **Verify raw body**: Ensure you're using raw request body, not parsed JSON
3. **Check header name**: Should be `X-Sonotheia-Signature`

### Duplicate Events

1. **Implement idempotency**: Track processed event IDs
2. **Use event.id field**: Sonotheia provides unique event IDs
3. **Set reasonable TTL**: Clean up old event IDs periodically

### Rate Limit Errors

1. **Check rate limit configuration**: Adjust `RATE_LIMIT_MAX_REQUESTS` if needed
2. **Monitor traffic**: Check if legitimate traffic or abuse
3. **Consider IP whitelisting**: If possible, whitelist Sonotheia IPs

## Best Practices

1. **Always verify signatures** in production
2. **Implement idempotency** to handle duplicate deliveries
3. **Use HTTPS** for all webhook endpoints
4. **Set request size limits** to prevent DoS
5. **Log all events** (without sensitive data)
6. **Store results persistently** (database, not memory)
7. **Monitor webhook health** with health check endpoints
8. **Handle errors gracefully** (return appropriate status codes)
9. **Test thoroughly** before production deployment
10. **Document your webhook URL** and keep it updated

## Related Documentation

- [Webhook Schemas](WEBHOOK_SCHEMAS.md) - Complete event payload schemas
- [Best Practices](BEST_PRACTICES.md) - Production integration patterns
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
- [Python Webhook Receiver](../examples/python/webhook_receiver/README.md) - FastAPI implementation
- [Node.js Webhook Server](../examples/node/webhook-server.js) - Express implementation
