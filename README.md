# Sonotheia Examples

Research harness for stress-testing synthetic speech detection: calibrated deferral, evidence-first outputs, voice MFA, and SAR workflows.

> **Note:** The Sonotheia API (for Sonotheia.ai) is hosted at `https://api.sonotheia.com`.

> This repo is an integration and evaluation reference, not a production SDK. It emphasizes repeatable tests, calibrated deferral, and structured review when outputs are uncertain.

## Quickstart
1. Copy `.env.example` to `.env` and add your credentials:
   ```bash
   cp .env.example .env
   # Edit .env and set SONOTHEIA_API_KEY=your_actual_key
   ```

2. Or export environment variables directly:
   ```bash
   export SONOTHEIA_API_URL=https://api.sonotheia.com  # Canonical API host for Sonotheia.ai
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

The evaluation scaffold supports slicing audio into short windows (10–15s), running repeatable perturbation tests, and capturing audit-grade records of measurements and decisions.

## Examples

### cURL

Minimal scripts for quick API testing. Requires `SONOTHEIA_API_KEY` environment variable.

```bash
# Deepfake detection
./examples/curl/deepfake-detect.sh audio.wav

# Voice MFA verification
SONOTHEIA_ENROLLMENT_ID=enroll-123 ./examples/curl/mfa-verify.sh audio.wav

# SAR generation
./examples/curl/sar-report.sh session-123 review "Manual review"
```

### Python

Python client with retry logic, rate limiting, and circuit breakers. Requires Python 3.9+.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r examples/python/requirements.txt
python examples/python/main.py audio.wav --enrollment-id enroll-123
```

See [examples/python/README.md](examples/python/README.md) for enhanced features and deployment.

### TypeScript

Type-safe client with full type definitions. Requires Node.js 18+.

```bash
cd examples/typescript
npm install && npm run build
export SONOTHEIA_API_KEY=YOUR_API_KEY
node dist/index.js audio.wav --enrollment-id enroll-123
```

### Node.js

Batch processing and webhook server examples.

```bash
# Batch processor
cd examples/node && npm install
export SONOTHEIA_API_KEY=YOUR_API_KEY
node batch-processor.js /path/to/*.wav

# Webhook server
PORT=3000 SONOTHEIA_WEBHOOK_SECRET=your_secret node webhook-server.js
```

See [examples/node/README.md](examples/node/README.md) for advanced patterns.

## Advanced Features

For retries, rate limiting, circuit breakers, streaming, monitoring, and Kubernetes deployment:
- [Enhanced Examples Guide](docs/ENHANCED_EXAMPLES.md)
- [Python README](examples/python/README.md)
- [Node.js README](examples/node/README.md)
- [Kubernetes README](examples/kubernetes/README.md)

## Output Format

Example response (illustrative). Ambiguous outcomes should trigger deferral and structured review.

```json
{
  "deepfake": {"score": 0.82, "recommended_action": "defer_to_review", "latency_ms": 640},
  "mfa": {"verified": true, "enrollment_id": "enroll-123", "confidence": 0.93},
  "sar": {"status": "submitted", "case_id": "sar-001234"}
}
```

## Notes
- Send short (<10s) mono WAV or Opus audio for best latency
- Never hard-code API keys in source control
- Replace placeholder IDs with actual values from your environment

## Documentation

### User Documentation
- [FAQ](docs/FAQ.md) - Common questions
- [Best Practices](docs/BEST_PRACTICES.md) - Integration guide
- [Enhanced Examples](docs/ENHANCED_EXAMPLES.md) - Advanced features
- [Repository Structure](docs/REPOSITORY_STRUCTURE.md) - How this repo is organized
- [License Information](docs/LICENSE_INFO.md) - Understanding the MIT License for this repository

### AI-Assisted Development Workflow
- [AI Development Workflow](.github/QUICK_REFERENCE.md) - Complete workflow guide
- [Start Simple](docs/03-workflow-building/start-simple.md) - Three-question framework
- [Multi-Agent Workflow](docs/03-workflow-building/multi-agent-workflow.md) - Multiple AI checks
- [Learning Journal Template](templates/learning-journal.md) - Track your progress

### For Contributors
- [Coding Standards](.github/CODING_STANDARDS.md) - Complete standards and guidelines
- [Agent Quick Reference](.github/AGENT_QUICK_REFERENCE.md) - Quick reference for agents

## Testing

Run tests locally:

```bash
# Python
cd examples/python
pip install -r requirements.txt
pytest tests/ -v

# TypeScript
cd examples/typescript
npm install && npm run build

# Node.js
cd examples/node
npm install
node --check batch-processor.js
```

## License

This repository is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

**Note:** This license applies to the example code and documentation in this repository only. Access to the Sonotheia API service requires separate authorization. For detailed information about the license, see [docs/LICENSE_INFO.md](docs/LICENSE_INFO.md).

---

**Support:** Contact your Sonotheia integration engineer  
**API Reference:** Available on request
