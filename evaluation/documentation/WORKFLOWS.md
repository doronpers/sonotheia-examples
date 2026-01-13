# Common Workflows

Here are three common ways to integrate the Audio Trust Harness into production pipelines.

## 1. Content Moderation Triage

**Goal:** Reduce human moderator fatigue by filtering out "technically broken" audio before they listen.

**Workflow:**

1. **Ingest** user report (audio file).
2. **Run Harness:**

   ```bash
   python -m audio_trust_harness run --audio suspect.wav --out audit.jsonl --fragility-threshold 0.4
   ```

3. **Branch:**
   - `insufficient_evidence`: Auto-reject ticket ("Audio unclear").
   - `defer_to_review`: **Priority Queue**. This audio is weird, glitchy, or fragile. Human needs to check.
   - `accept`: Send to standard moderation queue or automated classifier.

---

## 2. Call Center QA Sampling

**Goal:** Ensure voice biometric enrollment audio is high quality.

**Workflow:**

1. **Record** enrollment phrase (3 channel setup).
2. **Run Harness** with strict thresholds:

   ```bash
   python -m audio_trust_harness run --audio enrollment.wav --out audit.jsonl --clipping-threshold 0.9 --min-duration 3.0
   ```

3. **Logic:**
   - If *any* slice returns `defer_to_review` or `insufficient_evidence`: **Reject Enrollment**.
   - Ask user to "Please speak closer to the mic" or "Move to a quieter room".
   - Only allow enrollment if outcome is `accept`.

---

## 3. Pre-Ingestion Quality Gating (ML Training)

**Goal:** Clean a dataset of 100k hours of audio before training a TTS or STT model.

**Workflow:**

1. **Batch Process** entire dataset (parallelized).
2. **Summary Analysis:**

   ```bash
   python -m audio_trust_harness summary --audit dataset_audit.jsonl --out report.json
   ```

3. **Filter:**
   - Drop all files marked `insufficient_evidence` (removes silence/garbage).
   - Drop all files with `fragility_score > 0.5` (removes highly unstable recordings).
   - Stratify the remaining `accept` files by their indicator variance to ensure dataset diversity.

---

## Performance Tuning

| Use Case | Suggested `slice_seconds` | `fragility_threshold` | Why? |
| :--- | :--- | :--- | :--- |
| **Moderation** | 5.0 | 0.4 | Faster processing; focus on major glitches. |
| **Biometrics** | 2.0 | 0.25 | Verify short phrases; high standard for quality. |
| **Dataset Cleaning** | 30.0 | 0.3 | Long context; balance yield vs. quality. |
