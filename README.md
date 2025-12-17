# Sonotheia Examples

Integration examples and documentation for the Sonotheia voice fraud detection API: deepfake detection, voice MFA, and SAR generation.

## Quickstart
1. Export your credentials and base URL (use the defaults if you are on the public cloud endpoint):
   ```bash
   export SONOTHEIA_API_URL=https://api.sonotheia.com
   export SONOTHEIA_API_KEY=YOUR_API_KEY
   # Optional: override endpoint paths if your deployment differs from defaults
   # export SONOTHEIA_DEEPFAKE_PATH=/v1/voice/deepfake
   # export SONOTHEIA_MFA_PATH=/v1/mfa/voice/verify
   # export SONOTHEIA_SAR_PATH=/v1/reports/sar
   ```
2. Pick an example:
   - **cURL** one-liners under `examples/curl` for quick smoke tests.
   - **Python** helper in `examples/python` for scripted flows.
3. Provide an audio file (16 kHz mono WAV recommended) and run the example.

## Repository layout
- `examples/curl/` – minimal cURL scripts for the three primary flows.
- `examples/python/` – small helper demonstrating deepfake scoring, MFA verification, and SAR creation.
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
./examples/curl/sar-report.sh session-123 --decision review --reason "Manual review requested"
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
