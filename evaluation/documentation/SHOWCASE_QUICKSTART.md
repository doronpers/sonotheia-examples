# Showcase Quickstart

**Time to complete:** ~5 minutes

The **Audio Trust Harness** is a robustness evaluation tool that stress-tests audio against common perturbations (noise, compression, clipping) to determine if it is "stable enough" for reliable analysis.

It produces **deferral signals** (accept, defer, insufficient evidence), *not* deepfake detection verdicts.

---

## 1. Setup

Install the package and its dependencies. We recommend a virtual environment.

```bash
# Clone and enter repo
git clone https://github.com/doronpers/audio-trust-harness.git
cd audio-trust-harness

# Create venv
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install -e .
```

---

## 2. Run the Demo

The harness comes with a built-in demo mode that generates safe, synthetic test assets and runs a full evaluation against them.

```bash
# Run the demo validation
python -m audio_trust_harness run --demo --out out/demo_audit.jsonl
```

You should see output indicating that synthetic audio (clean, noisy, clipped) is being generated and processed.

Now, generate a summary report:

```bash
# Summarize the results
python -m audio_trust_harness summary \
  --audit out/demo_audit.jsonl \
  --out out/demo_summary.json \
  --print-summary
```

---

## 3. Interpret the Results

You will see a summary printed to your terminal. Here is what to look for:

### Deferral Actions

- **accept**: The audio is robust. Indicators remained stable across mild perturbations.
- **defer_to_review**: The audio is **fragile**. Perturbations caused significant shifts in indicators. A human should review this slice.
- **insufficient_evidence**: The audio was too short, silent, or heavily clipped to make a reliable determination.

### Fragility Score

A number between 0.0 and 1.0.

- **Low (< 0.1)**: Very stable.
- **High (> 0.3)**: High variance (Coefficient of Variation) in indicators.

### Example Output Snippet

```json
{
  "deferral_action": "defer_to_review",
  "fragility_score": 0.45,
  "reasons": ["high_indicator_variance"]
}
```

---

## What Next?

- [Interpreting Results](INTERPRETING_RESULTS.md) - Deep dive into the metrics
- [Workflows](WORKFLOWS.md) - How to integrate this into moderation or QA pipelines
- Review `out/demo_summary.json` to see the full aggregate statistics
