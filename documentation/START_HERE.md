# Start Here: Sonotheia Examples

> **Goal**: Pick the right track and run your first successful command in minutes.

This repository has two complementary tracks. Choose the one that matches your goal:

1. **Integration Examples** → production API integration patterns (Python/TypeScript/Node/cURL)
2. **Evaluation Framework** → research harness for robustness testing (Audio Trust Harness)

---

## Track A: Integration Examples (Production)

**Best for:** teams integrating the Sonotheia API into apps or services.

### Fastest path (cURL, ~2 minutes)

```bash
export SONOTHEIA_API_KEY=your_api_key_here

curl -X POST https://api.sonotheia.com/v1/voice/deepfake \
  -H "Authorization: Bearer ${SONOTHEIA_API_KEY}" \
  -H "Accept: application/json" \
  -F "audio=@path/to/your/audio.wav" \
  -F 'metadata={"session_id":"test-session"};type=application/json'
```

### Production path (Python, ~5 minutes)

```bash
cd examples/python
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

export SONOTHEIA_API_KEY=your_api_key_here
python main.py path/to/your/audio.wav
```

**Next steps**
- Integration quickstart: [Getting Started](GETTING_STARTED.md)
- Full integration guide: [examples/README.md](../examples/README.md)

---

## Track B: Evaluation Framework (Research)

**Best for:** researchers or evaluators stress-testing indicator robustness.

### Fastest path (demo mode, ~5 minutes)

```bash
cd evaluation
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

python -m audio_trust_harness run --demo --out out/demo_audit.jsonl \
  --summary-out out/demo_summary.json \
  --dashboard-out out/demo_dashboard.html
```

**Next steps**
- Evaluation quickstart: [Showcase Quickstart](../evaluation/documentation/SHOWCASE_QUICKSTART.md)
- Full evaluation guide: [evaluation/README.md](../evaluation/README.md)

---

## Need help?

- Documentation index: [documentation/INDEX.md](INDEX.md)
- FAQ: [documentation/FAQ.md](FAQ.md)
- Troubleshooting: [documentation/TROUBLESHOOTING.md](TROUBLESHOOTING.md)
