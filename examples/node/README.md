# Sonotheia Node.js Examples

> **Advanced integration patterns** including batch processing, webhook servers, and async queue management.

Production-ready examples for the Sonotheia voice fraud detection API.

## Examples

### 1. Batch Processor

Process multiple audio files concurrently with rate limiting and summary statistics.

**Features:**
- Concurrent processing with configurable limits
- Progress tracking and detailed logging
- Summary statistics (average scores, risk distribution)
- Error handling and retry logic

**Usage:**

```bash
npm install

# Process individual files
SONOTHEIA_API_KEY=xxx node batch-processor.js file1.wav file2.wav file3.wav

# Process entire directory
SONOTHEIA_API_KEY=xxx node batch-processor.js /path/to/audio/files/

# With custom concurrency
CONCURRENT_REQUESTS=10 SONOTHEIA_API_KEY=xxx node batch-processor.js *.wav
```

**Environment Variables:**
- `SONOTHEIA_API_KEY` - Required API key
- `SONOTHEIA_API_URL` - Sonotheia API endpoint (default: https://api.sonotheia.com)
- `CONCURRENT_REQUESTS` - Max concurrent requests (default: 5)
- `LOG_LEVEL` - Logging level: debug, info, warn, error (default: info)

**Note**: Examples read from process environment variables. They do NOT automatically load `.env` files. To use a `.env` file, you'll need to use a tool like `dotenv` or export variables manually: `export $(cat .env | xargs)`.

**Output:**
```
=== BATCH PROCESSING RESULTS ===

Total files:     50
Successful:      48
Failed:          2
Average score:   0.342

Risk distribution:
  High (>0.7):   3
  Medium (0.4-0.7): 12
  Low (<0.4):    33

Total duration:  45.23s
Avg per file:    904ms
```

### 2. Webhook Server

Example Express server for receiving asynchronous API callbacks.

**Features:**
- Webhook signature verification
- Multiple event type handling
- Result storage and retrieval
- Health check endpoint

**Usage:**

```bash
npm install

# Start server
PORT=3000 SONOTHEIA_WEBHOOK_SECRET=your_secret node webhook-server.js
```

**Endpoints:**

- `POST /webhook` - Receive webhook events
- `GET /health` - Health check
- `GET /results/:session_id` - Get specific result
- `GET /results` - List all results

**Supported Events:**
- `deepfake.completed` - Deepfake detection finished
- `mfa.completed` - MFA verification finished
- `sar.submitted` - SAR submission confirmed

**Example Webhook Payload:**
```json
{
  "type": "deepfake.completed",
  "data": {
    "session_id": "session-123",
    "score": 0.85,
    "recommended_action": "defer_to_review",
    "timestamp": "2025-01-04T12:00:00Z"
  }
}
```

**Testing Locally:**

```bash
# Start server
node webhook-server.js

# Send test webhook (in another terminal)
curl -X POST http://localhost:3000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "type": "deepfake.completed",
    "data": {
      "session_id": "test-123",
      "score": 0.75,
      "recommended_action": "defer_to_review",
      "timestamp": "2025-01-04T12:00:00Z"
    }
  }'

# Check results
curl http://localhost:3000/results/test-123
```

## Operational Considerations

### Batch Processor
- Use a proper task queue (Bull, BullMQ) for production
- Implement retry logic with exponential backoff
- Store results in a database, not in memory
- Add metrics and monitoring
- Consider rate limiting per API terms

### Webhook Server
- **Always** verify webhook signatures in production
- Use a database instead of in-memory storage
- Implement idempotency (handle duplicate webhooks)
- Add authentication for result endpoints
- Use a reverse proxy (nginx) in front of Express
- Enable HTTPS/TLS
- Add request rate limiting (e.g., express-rate-limit)
- Implement proper logging and alerting

## Error Handling

Both examples include comprehensive error handling:

```javascript
try {
  const result = await processFile(audioPath);
  logger.info({ result }, 'Processing successful');
} catch (error) {
  if (error.response) {
    // API returned an error
    logger.error({ status: error.response.status, data: error.response.data });
  } else if (error.request) {
    // No response received
    logger.error('No response from API');
  } else {
    // Other errors
    logger.error({ error: error.message });
  }
}
```

## Logging

Uses `pino` for structured JSON logging:

```bash
# Set log level
LOG_LEVEL=debug node batch-processor.js

# Pretty print logs (development)
node batch-processor.js | pino-pretty
```

## Requirements

- **Node.js**: 18 or later
- **Dependencies**: See `package.json`

## 📌 Quick Links

- [Getting Started Guide](../../documentation/GETTING_STARTED.md) — 5-minute setup
- [Documentation Index](../../documentation/INDEX.md) — find anything quickly
- [Examples Overview](../README.md) — quick-start commands for every language
- [FAQ](../../documentation/FAQ.md) — common questions and troubleshooting
- [Best Practices](../../documentation/BEST_PRACTICES.md) — production integration guidelines
