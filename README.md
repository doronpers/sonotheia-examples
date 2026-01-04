# Sonotheia Examples

Integration examples and documentation for the Sonotheia voice fraud detection API: deepfake detection, voice MFA, and SAR generation.

> This repository contains integration examples plus an experimental evaluation harness scaffold; it is not a production SDK.

## Quickstart
1. Copy `.env.example` to `.env` and add your credentials:
   ```bash
   cp .env.example .env
   # Edit .env and set SONOTHEIA_API_KEY=your_actual_key
   ```

2. Or export environment variables directly:
   ```bash
   export SONOTHEIA_API_URL=https://api.sonotheia.com
   export SONOTHEIA_API_KEY=YOUR_API_KEY
   # Optional: override endpoint paths if your deployment differs from defaults
   # export SONOTHEIA_DEEPFAKE_PATH=/v1/voice/deepfake
   # export SONOTHEIA_MFA_PATH=/v1/mfa/voice/verify
   # export SONOTHEIA_SAR_PATH=/v1/reports/sar
   ```

3. Pick an example:
   - **cURL** one-liners under `examples/curl` for quick smoke tests.
   - **Python** helper in `examples/python` for scripted flows.
   - **TypeScript** type-safe client in `examples/typescript`.
   - **Node.js** advanced patterns in `examples/node`.

4. Provide an audio file (16 kHz mono WAV recommended) and run the example.

## Repository layout
- `examples/curl/` – minimal cURL scripts for the three primary flows.
- `examples/python/` – small helper demonstrating deepfake scoring, MFA verification, and SAR creation.
  - **Enhanced examples**: Production-ready clients with retry logic, rate limiting, circuit breakers, and streaming support
- `examples/typescript/` – type-safe TypeScript client with full type definitions.
- `examples/node/` – advanced Node.js examples including batch processing and webhook server.
  - **Enhanced examples**: Monitoring, metrics, and observability features
- `examples/kubernetes/` – Kubernetes deployment manifests for production environments.
- `docs/` – comprehensive documentation including FAQ, best practices, and troubleshooting.
- `LICENSE` – project license.

## cURL examples
The scripts require `SONOTHEIA_API_KEY` to be set. You can override `SONOTHEIA_API_URL` or the individual `*_PATH` variables if your stack uses different routes.

```bash
# Deepfake detection
./examples/curl/deepfake-detect.sh path/to/audio.wav

# Voice MFA verification (pass enrollment ID)
SONOTHEIA_ENROLLMENT_ID=enroll-123 \
  ./examples/curl/mfa-verify.sh path/to/audio.wav

# Generate a SAR from a prior session
./examples/curl/sar-report.sh session-123 review "Manual review requested"
```

## Python example
Requirements: Python 3.9+ and `requests`.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r examples/python/requirements.txt
python examples/python/main.py path/to/audio.wav \
  --enrollment-id enroll-123 \
  --session-id session-123
```

Outputs are printed as formatted JSON so you can copy/paste into dashboards or support tickets.

## TypeScript example
Requirements: Node.js 18+ and npm.

```bash
cd examples/typescript
npm install
npm run build
export SONOTHEIA_API_KEY=YOUR_API_KEY
node dist/index.js path/to/audio.wav \
  --enrollment-id enroll-123 \
  --session-id session-123
```

Features type-safe interfaces for all API endpoints with comprehensive error handling.

## Node.js advanced examples

### Batch Processor
Process multiple audio files concurrently:

```bash
cd examples/node
npm install
export SONOTHEIA_API_KEY=YOUR_API_KEY
node batch-processor.js /path/to/audio/*.wav
```

### Webhook Server
Example server for receiving async API callbacks:

```bash
cd examples/node
npm install
PORT=3000 SONOTHEIA_WEBHOOK_SECRET=your_secret node webhook-server.js
```

## Enhanced Examples

### Production-Ready Features

The enhanced examples include production-ready features:

#### Python Enhanced Client (`examples/python/client_enhanced.py`)
```bash
python examples/python/enhanced_example.py audio.wav \
  --max-retries 5 \
  --rate-limit 2.0 \
  --enrollment-id enroll-123
```

Features:
- **Retry logic** with exponential backoff
- **Rate limiting** using token bucket algorithm
- **Circuit breaker** pattern for fault tolerance
- **Connection pooling** for better performance
- **Comprehensive error handling**

#### Streaming Audio Processing (`examples/python/streaming_example.py`)
```bash
python examples/python/streaming_example.py long_audio.wav \
  --chunk-duration 10
```

Features:
- Process large audio files by splitting into chunks
- Memory-efficient processing
- Progress tracking and aggregated results
- Automatic SAR submission for high-risk content

#### Health Checks and Monitoring (`examples/python/health_check.py`)
```bash
# Single health check
python examples/python/health_check.py

# Continuous monitoring
python examples/python/health_check.py --monitor --interval 60

# Prometheus metrics export
python examples/python/health_check.py --prometheus-port 9090
```

Features:
- API connectivity verification
- Authentication validation
- Prometheus metrics export
- Kubernetes readiness/liveness probes

#### Enhanced Batch Processor (`examples/node/batch-processor-enhanced.js`)
```bash
SONOTHEIA_API_KEY=xxx node examples/node/batch-processor-enhanced.js *.wav
```

Features:
- Circuit breaker with automatic recovery
- Retry logic with exponential backoff
- Prometheus metrics endpoint
- Health check endpoint
- Structured logging with pino

### Docker and Kubernetes

#### Docker Support
```bash
cd examples/python
docker build -t sonotheia-python .
docker run -e SONOTHEIA_API_KEY=xxx -v $(pwd)/audio:/audio sonotheia-python python main.py /audio/sample.wav
```

Or use Docker Compose:
```bash
cd examples/python
docker-compose up sonotheia-enhanced
```

#### Kubernetes Deployment
```bash
# Deploy to Kubernetes
kubectl apply -f examples/kubernetes/deployment.yaml

# Check status
kubectl get pods -l app=sonotheia-processor

# View metrics
kubectl port-forward svc/sonotheia-processor-metrics 9090:9090
curl http://localhost:9090/metrics
```

See [Kubernetes README](examples/kubernetes/README.md) for detailed documentation.

## Sample responses
```json
{
  "deepfake": {"score": 0.82, "label": "likely_real", "latency_ms": 640},
  "mfa": {"verified": true, "enrollment_id": "enroll-123", "confidence": 0.93},
  "sar": {"status": "submitted", "case_id": "sar-001234"}
}
```

## Notes
- All examples rely on bearer token authentication; never hard-code secrets in source control.
- For best latency, send short (<10s) mono WAV or Opus audio.
- Replace placeholder IDs (session/enrollment) with values from your environment or preceding API calls.

## Documentation
- [FAQ](docs/FAQ.md) - Common questions and answers
- [Best Practices](docs/BEST_PRACTICES.md) - Comprehensive integration guide
- [NOTES](NOTES.md) - Assumptions, TODOs, and questions for implementation
- [TypeScript README](examples/typescript/README.md) - TypeScript-specific documentation
- [Node.js README](examples/node/README.md) - Advanced integration patterns
- [Python README](examples/python/README.md) - Python client library documentation
- [Kubernetes README](examples/kubernetes/README.md) - Production deployment guide

## Development

This repository includes:
- **Unit tests** for Python client (see `examples/python/tests/`)
- **CI/CD pipeline** via GitHub Actions for linting and testing
- **Code quality tools**: pytest, ruff (Python), TypeScript compiler

To run tests locally:
```bash
# Python tests
cd examples/python
pip install -r requirements.txt
pytest tests/ -v

# TypeScript build
cd examples/typescript
npm install
npm run build

# Node.js syntax check
cd examples/node
npm install
node --check batch-processor.js
node --check webhook-server.js
```

## Additional Resources
- API Reference: Available on request
- Support: Contact your Sonotheia integration engineer
