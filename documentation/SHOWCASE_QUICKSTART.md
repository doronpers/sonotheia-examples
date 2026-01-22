# Showcase Quickstart Guide

> **Goal**: Run a complete Sonotheia workflow demo in minutes—no API key required for mock mode.

This guide shows you how to run the **Golden Path** demo—a complete end-to-end workflow that demonstrates deepfake detection, voice MFA verification, routing decisions, and optional SAR submission.

## Three Ways to Run

### 1. Mock Mode (No API Key Required)

Perfect for exploring the workflow without API credentials or consuming quota.

**Python:**
```bash
cd examples/python
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Start mock server in one terminal
python mock_api_server.py

# In another terminal, run golden path demo
python golden_path_demo.py ../test-audio/clean_tone.wav --mock
```

**TypeScript:**
```bash
cd examples/typescript
npm install && npm run build

# Start mock server (Python)
cd ../python
python mock_api_server.py

# In another terminal, run golden path demo
cd ../typescript
npm run golden-path -- ../test-audio/clean_tone.wav --mock
```

**What you'll see:**
- Complete workflow output in JSON format
- Deepfake detection results
- MFA verification (if enrollment ID provided)
- Routing decision based on results
- Optional SAR submission

### 2. Real API Mode (Requires API Key)

Use the actual Sonotheia API for production-like testing.

**Python:**
```bash
cd examples/python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export SONOTHEIA_API_KEY=your_api_key_here
python golden_path_demo.py audio.wav
```

**TypeScript:**
```bash
cd examples/typescript
npm install && npm run build

export SONOTHEIA_API_KEY=your_api_key_here
npm run golden-path -- audio.wav
```

**With MFA verification:**
```bash
# Python
python golden_path_demo.py audio.wav --enrollment-id enroll-123

# TypeScript
npm run golden-path -- audio.wav --enrollment-id enroll-123
```

**With SAR submission:**
```bash
# Python
python golden_path_demo.py audio.wav \
  --session-id session-123 \
  --sar auto

# TypeScript
npm run golden-path -- audio.wav \
  --session-id session-123 \
  --sar auto
```

### 3. Webhook Mode (Enterprise Pattern)

Test webhook integration for asynchronous processing.

**Setup:**
1. Start webhook receiver (Python or Node.js)
2. Configure webhook URL in your Sonotheia account
3. Run golden path demo with webhook callback

**Python Webhook Receiver:**
```bash
cd examples/python/webhook_receiver
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start webhook server
python app.py
# Server runs on http://localhost:8080/webhook
```

**Node.js Webhook Receiver:**
```bash
cd examples/node
npm install

# Start webhook server
node webhook-server.js
# Server runs on http://localhost:8080/webhook
```

**Trigger webhook:**
```bash
# Python
python golden_path_demo.py audio.wav \
  --webhook-url http://localhost:8080/webhook

# TypeScript
npm run golden-path -- audio.wav \
  --webhook-url http://localhost:8080/webhook
```

## Understanding the Output

The Golden Path demo outputs a standardized JSON contract:

```json
{
  "session_id": "demo-session-123",
  "timestamp": "2026-01-21T12:00:00Z",
  "inputs": {
    "audio_filename": "audio.wav",
    "audio_seconds": 7.2,
    "samplerate_hz": 16000
  },
  "results": {
    "deepfake": {
      "score": 0.82,
      "label": "likely_synthetic",
      "recommended_action": "defer_to_review",
      "latency_ms": 640
    },
    "mfa": {
      "verified": true,
      "enrollment_id": "enroll-123",
      "confidence": 0.93
    },
    "sar": {
      "status": "submitted",
      "case_id": "sar-001234"
    }
  },
  "decision": {
    "route": "ESCALATE_TO_HUMAN",
    "reasons": ["deepfake_defer", "high_value_transaction"],
    "explainability": {
      "human_summary": "Risk ambiguous; escalate for manual review."
    }
  },
  "diagnostics": {
    "request_id": "req-abc123",
    "retries": 1
  }
}
```

### Key Fields Explained

- **`results.deepfake`**: Deepfake detection score (0.0-1.0), label, and recommended action
- **`results.mfa`**: Voice MFA verification result (only if enrollment ID provided)
- **`results.sar`**: SAR submission status (only if SAR submitted)
- **`decision.route`**: Final routing decision (ALLOW, REQUIRE_STEP_UP, REQUIRE_CALLBACK, ESCALATE_TO_HUMAN, BLOCK)
- **`decision.reasons`**: List of reason codes explaining the decision
- **`decision.explainability`**: Human-readable summary

### Routing Decisions

The demo makes routing decisions based on:

- **ALLOW**: Low risk, standard processing
- **REQUIRE_STEP_UP**: Medium risk, additional verification needed (e.g., SMS OTP)
- **REQUIRE_CALLBACK**: Medium-high risk, outbound callback required
- **ESCALATE_TO_HUMAN**: Low confidence or high risk, manual review needed
- **BLOCK**: Critical risk, transaction blocked

## Command-Line Options

### Python Golden Path Demo

```bash
python golden_path_demo.py <audio_file> [OPTIONS]

Options:
  --enrollment-id ID    Enrollment ID for MFA verification
  --session-id ID       Session identifier (auto-generated if not provided)
  --sar MODE            SAR submission mode: auto, never, always (default: auto)
  --mock                Use mock API server instead of real API
  --api-url URL         Override API URL (default: https://api.sonotheia.com)
  --output FILE         Write JSON output to file
  --pretty              Pretty-print JSON output
  --verbose             Enable verbose logging
```

### TypeScript Golden Path Demo

```bash
npm run golden-path -- <audio_file> [OPTIONS]

Options:
  --enrollment-id <id>  Enrollment ID for MFA verification
  --session-id <id>     Session identifier
  --sar <mode>          SAR submission mode: auto, never, always
  --mock                Use mock API server
  --api-url <url>       Override API URL
  --output <file>       Write JSON output to file
  --pretty              Pretty-print JSON output
```

## Troubleshooting

### "API key required" error in mock mode

**Solution**: Use the `--mock` flag to bypass API key requirement:
```bash
python golden_path_demo.py audio.wav --mock
```

### Mock server not responding

**Solution**: Ensure mock server is running:
```bash
# Check if running
curl http://localhost:8000/health

# Start if not running
cd examples/python
python mock_api_server.py
```

### Audio file format errors

**Solution**: Ensure audio file is in supported format (WAV, Opus, MP3, FLAC) and meets requirements:
- Sample rate: 8kHz - 48kHz
- Duration: 1-300 seconds
- File size: < 50MB (or use streaming for larger files)

### Enrollment ID not found

**Solution**: Enrollment IDs must be obtained out-of-band. For testing:
- Use mock mode with `--enrollment-id test-enrollment-123`
- Contact your Sono Platform integration engineer for production enrollment IDs

### Network timeouts

**Solution**: 
- Check your internet connection
- Verify API URL is correct: `https://api.sonotheia.com`
- Try increasing timeout (if supported by client)
- Use mock mode for offline testing

### JSON parsing errors

**Solution**: Ensure output is valid JSON:
```bash
# Validate JSON output
python -m json.tool output.json

# Or use jq
cat output.json | jq .
```

## Next Steps

After running the Golden Path demo:

1. **Explore Advanced Examples**
   - [Enhanced Client](examples/python/README.md#enhanced-client) - Retry logic, circuit breakers
   - [Streaming Processor](examples/python/README.md#streaming-audio-processor) - Large file handling
   - [Voice Routing](examples/python/README.md#voice-integrity-routing) - Financial services patterns

2. **Read Integration Guides**
   - [Best Practices](BEST_PRACTICES.md) - Production integration patterns
   - [MFA Enrollment](MFA_ENROLLMENT.md) - Voice enrollment workflows
   - [Webhook Integration](WEBHOOK_END_TO_END.md) - Asynchronous processing

3. **Evaluate Robustness**
   - [Evaluation Framework](../evaluation/README.md) - Stress-test indicators
   - [Showcase Quickstart](../evaluation/documentation/SHOWCASE_QUICKSTART.md) - Research workflows

## Getting Help

- **Documentation**: [Documentation Index](INDEX.md)
- **FAQ**: [Frequently Asked Questions](FAQ.md)
- **Troubleshooting**: [Troubleshooting Guide](TROUBLESHOOTING.md)
- **Issues**: [GitHub Issues](https://github.com/doronpers/sonotheia-examples/issues)
- **Support**: Contact your Sono Platform integration engineer

---

**Ready to integrate?** Start with the [Getting Started Guide](GETTING_STARTED.md) for detailed setup instructions.
