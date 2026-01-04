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
- `examples/typescript/` – type-safe TypeScript client with full type definitions.
- `examples/node/` – advanced Node.js examples including batch processing and webhook server.
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
