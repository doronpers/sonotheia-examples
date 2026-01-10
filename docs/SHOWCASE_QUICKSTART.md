# Showcase Quickstart: The Golden Path

> **Goal:** Run the "Golden Path" demo in 2 minutes—with or without an API key.

This guide showcases the Sonotheia integration workflow using our "Golden Path" demo scripts. You'll see deepfake detection, voice MFA, and risk routing in a single, unified JSON output.

---

## 1. Mock Mode (No API Key Required)

Don't have an API key yet? You can still experience the full workflow using the built-in mock mode.

### Python

```bash
# 1. Setup
cd examples/python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Run in Mock Mode
#    We use a test file included in the repo
python golden_path_demo.py ../test-audio/deepfake-sample.wav --mock
```

### TypeScript

```bash
# 1. Setup
cd examples/typescript
npm install
npm run build

# 2. Run in Mock Mode
npm run golden-path -- ../test-audio/deepfake-sample.wav --mock
```

**What you'll see:**  
A complete JSON output simulating a "likely synthetic" result, including a routing decision to `ESCALATE_TO_HUMAN`.

---

## 2. Real API Mode (API Key Required)

Ready to test with the real Sonotheia API?

### Python

```bash
# 1. Set API Key
export SONOTHEIA_API_KEY=your_actual_key

# 2. Run with Real Audio
python golden_path_demo.py ../test-audio/real-human-sample.wav
```

### TypeScript

```bash
# 1. Set API Key
export SONOTHEIA_API_KEY=your_actual_key

# 2. Run
npm run golden-path -- ../test-audio/real-human-sample.wav
```

**Optional Flags:**

- `--enrollment-id <id>`: Also attempts to verify the speaker against an enrolled voice profile.
- `--sar auto`: Automatically submits a Suspicious Activity Report (SAR) if the score is high.

---

## 3. Webhook Mode

Simulate an asynchronous workflow where results are delivered via webhook.

*(Coming Soon in Phase E - Watch this space!)*

---

## 4. Troubleshooting

### "File not found"

- Ensure you are running the command from the correct directory (`examples/python` or `examples/typescript`).
- Check that the audio file path is correct relative to your current location.

### "401 Unauthorized" (Real Mode)

- Double-check `echo $SONOTHEIA_API_KEY` to ensure your key is exported.
- If using `.env`, make sure the script is loading it (Python script does this automatically).

### "Module not found"

- **Python**: Ensure you activated your venv (`source .venv/bin/activate`).
- **TypeScript**: Ensure you ran `npm install` and `npm run build`.

### "Enrollment ID not found"

- If verifying MFA, you need a valid `enrollment_id`.
- **Note:** Public enrollment endpoints may be restricted. Contact your integration engineer for a test ID.

---

## Next Steps

- **[Python Golden Path Source](../examples/python/golden_path_demo.py)**: Examine the production-ready code.
- **[Integration Best Practices](BEST_PRACTICES.md)**: Security, retries, and error handling.
- **[Full Documentation Index](INDEX.md)**: Explore all available guides.
