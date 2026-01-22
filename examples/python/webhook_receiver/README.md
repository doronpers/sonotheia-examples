# Python Webhook Receiver

FastAPI-based webhook receiver for Sonotheia API callbacks.

## Features

- **Signature Verification**: HMAC-SHA256 signature verification
- **Idempotency**: Duplicate events are automatically ignored
- **Rate Limiting**: Configurable rate limiting (100 requests/minute default)
- **Request Size Limits**: Configurable max request size (10MB default)
- **Event Routing**: Handles deepfake, MFA, and SAR events
- **Result Storage**: In-memory storage with TTL cleanup
- **Health Checks**: Health and metrics endpoints

## Installation

```bash
cd webhook_receiver
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Set environment variables:

```bash
export SONOTHEIA_WEBHOOK_SECRET=your_webhook_secret_here
export PORT=8080  # Optional, defaults to 8080
export MAX_REQUEST_SIZE_MB=10  # Optional, defaults to 10MB
```

## Usage

### Start Server

```bash
# Direct execution
python app.py

# Or with uvicorn
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

### Endpoints

- **POST /webhook** - Receive webhook events
- **GET /health** - Health check and metrics
- **GET /results** - List all stored results
- **GET /results/{session_id}** - Get specific result

### Example Webhook Event

```json
{
  "type": "deepfake.completed",
  "id": "event-abc123",
  "data": {
    "session_id": "session-xyz789",
    "score": 0.82,
    "label": "likely_synthetic",
    "timestamp": "2026-01-21T12:00:00Z"
  }
}
```

## Security Features

1. **Signature Verification**: Validates `X-Sonotheia-Signature` header
2. **Rate Limiting**: 100 requests per minute per IP (configurable)
3. **Request Size Limits**: Prevents oversized payloads
4. **Idempotency**: Prevents duplicate processing

## Production Considerations

For production deployment:

1. **Use a Database**: Replace in-memory storage with PostgreSQL/Redis
2. **Add Authentication**: Protect endpoints with API keys or OAuth
3. **Enable HTTPS**: Use reverse proxy (nginx) for SSL termination
4. **Monitoring**: Add Prometheus metrics, logging aggregation
5. **Scaling**: Use multiple workers with uvicorn or deploy to Kubernetes

## Testing

```bash
# Test webhook endpoint
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -H "X-Sonotheia-Signature: test_signature" \
  -d '{
    "type": "deepfake.completed",
    "id": "test-event-123",
    "data": {
      "session_id": "test-session",
      "score": 0.5,
      "label": "uncertain"
    }
  }'

# Check health
curl http://localhost:8080/health

# Get results
curl http://localhost:8080/results/test-session
```

## Integration with Golden Path Demo

The golden path demo can trigger webhooks:

```bash
python golden_path_demo.py audio.wav \
  --webhook-url http://localhost:8080/webhook
```

See [documentation/WEBHOOK_END_TO_END.md](../../../documentation/WEBHOOK_END_TO_END.md) for complete integration guide.
