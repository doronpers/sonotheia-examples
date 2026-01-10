# SONOTHEIA_EXAMPLES_SHOWCASE_PLAN

**Repo:** `doronpers/sonotheia-examples`  
**Date:** 2026-01-10  
**Owner:** doronpers  
**Primary goal:** Update and optimize this repo to better showcase Sonotheia’s work with a “golden path” demo and curated showcase UX, while remaining public-safe and developer-friendly.

---

## 0) Non‑negotiables (must follow)

### Security & privacy

- Never log or print raw audio bytes, base64 audio, or PII.
- Never print API keys; redact secrets in logs and error messages.
- Webhook examples must include signature verification and idempotency guidance.

### Technical standards (project-wide)

- Convert numpy types to native Python types before JSON serialization.
- Temporary files must use secure patterns (`mkstemp` or equivalent) with correct fd handling.
- Tests must use real file descriptors (no `None` placeholders), and must verify cleanup.
- Docker images used by examples must include `ca-certificates` so HTTPS works reliably.
- Audio upload guidance: if nginx is used, set `client_max_body_size 100M` (and document strategies for >100MB / up to 800MB).

### Repo positioning

- This is an integration/examples repo, not a full production SDK.
- Do not reference proprietary/internal endpoints or internals from other private systems.
- If an API detail cannot be confirmed, document it explicitly rather than inventing it.

---

## 1) Current state quick assessment (what exists today)

`sonotheia-examples` already includes:

- Strong top-level `README.md` and `examples/README.md`
- Multi-language examples: cURL, Python, TypeScript, Node
- Many production patterns already (retry guidance, webhook verification examples, infra examples like Terraform)
- Docs index references and workflow guides
- `NOTES.md` explicitly calls out missing/unclear: MFA enrollment endpoint/process, webhook registration, error schema, rate limits, session_id behavior.

`audio-trust-harness` (separate repo) is already a well-written research harness with:

- Clear deferral philosophy (accept / defer_to_review / insufficient_evidence)
- CLI usage, JSONL audit outputs, summary generation
- Strong “research tool, not classifier” framing
- Roadmap items (including visualization)

We will improve both repos so that:

- `sonotheia-examples` is the “integration showcase”
- `audio-trust-harness` is the “evaluation/robustness showcase”
- Outputs and storylines align (deferral + auditability)

---

## 2) Desired outcome (“Showcase UX”)

A first-time user should be able to:

1. Run a single command (Python or TypeScript) and see an end-to-end workflow output:
   - deepfake analysis
   - voice MFA verify (if enrollment is available)
   - a routing decision (ALLOW / STEP_UP / CALLBACK / ESCALATE / BLOCK)
   - optional SAR submission (when risk or deferral requires it)
2. Understand how to:
   - run in **mock mode** (no API key)
   - run in **real API mode** (API key)
   - run a **webhook demo**
3. See consistent, audit-friendly output structure across languages.

---

## 3) Golden Path Output Contract (standardize across languages)

All golden-path scripts must output JSON with this top-level structure (fields optional if not available):

```json
{
  "session_id": "string",
  "timestamp": "ISO-8601",
  "inputs": {
    "audio_filename": "string",
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
    "request_id": "if-provided",
    "retries": 1
  }
}
```

Rules:

- Must be JSON-safe (no numpy scalars).
- Must not include secrets.
- If some endpoints are unavailable, keep the shape but omit the sub-object and explain in docs.

---

## 4) Implementation Plan for `sonotheia-examples` (Python + TypeScript)

### Phase A — Docs-first “Showcase UX”

**Add:**

- `docs/SHOWCASE_QUICKSTART.md`
  - 1. Mock mode
  - 1. Real API mode
  - 1. Webhook mode
  - 1. “If you get stuck” troubleshooting mini-section

**Update:**

- Root `README.md`: add “Golden Path (Python + TypeScript)” above the fold
- `examples/README.md`: move “Golden Path” to the top, with one-command runs

**Acceptance criteria:**

- A new developer can follow docs without reading other pages.

---

### Phase B — Python Golden Path demo (canonical)

**Create:**

- `examples/python/golden_path_demo.py`
  - Inputs:
    - audio file path
    - optional `--enrollment-id`
    - optional `--sar` (auto/never/always)
    - optional `--session-id` (if API expects client-supplied; otherwise generate)
    - `--mock` to force mock server usage
  - Behavior:
    - validate config (`SONOTHEIA_API_KEY`, `SONOTHEIA_API_URL`, endpoint paths)
    - send audio to deepfake endpoint
    - if enrollment-id given, call MFA verify
    - decide route:
      - if recommended_action is defer OR score above threshold -> escalate/step-up
      - if verified false -> step-up/callback
      - if high risk -> SAR submission (depending on policy)
    - output JSON contract above

**Ensure:**

- Proper temp file handling if any pre-processing is done (use `mkstemp` and close fd; ensure cleanup)
- Comprehensive error handling (timeouts, network, invalid audio, 4xx/5xx)
- No numpy leakage in JSON (add `convert_numpy_types` helper if any DSP values are included)

**Add tests:**

- `examples/python/tests/test_golden_path_demo.py`
  - Use `tmp_path` to create real test files
  - Use `monkeypatch` to mock HTTP client calls
  - Verify:
    - JSON schema keys exist
    - cleanup happens (temp files removed)
    - errors return a clean JSON error shape (or clear exception type), not stack traces

**Acceptance criteria:**

- Works offline in mock mode
- Produces stable output

---

### Phase C — TypeScript Golden Path demo (parallel, future-proof)

**Create:**

- `examples/typescript/src/goldenPath.ts` (or `src/golden_path.ts`)
- Add CLI entry (e.g., `npm run golden-path -- audio.wav`)
- Implement:
  - config loading (`SONOTHEIA_API_KEY`, `SONOTHEIA_API_URL`, endpoint paths)
  - multipart upload via `fetch` (Node 18+)
  - consistent output JSON contract

**Type safety:**

- Define TS types for request/response payloads.
- Parse responses defensively (forward-compatible field access).

**Add tests:**

- Basic unit test for:
  - response parsing
  - routing decision logic (pure functions)
- If test framework exists, integrate; otherwise add minimal `vitest` or `node:test`.

**Acceptance criteria:**

- `npm install && npm run build` succeeds
- Golden path script runs and outputs contract

---

### Phase D — Resolve “Enrollment dead-end” explicitly

The agent must determine which of the following is true and implement accordingly:

**Option 1: Enrollment endpoint exists**

- Add enrollment examples in Python + TypeScript (+ curl if easy)
- Update `docs/MFA_ENROLLMENT.md` with real endpoint path and payload.

**Option 2: Enrollment is not publicly available**

- Update docs and READMEs to:
  - clearly state how users obtain enrollment IDs (out-of-band)
  - provide mock enrollment behavior in mock server
  - remove any “magical” assumptions from examples.

**Acceptance criteria:**

- No example requires `enrollment_id` without explaining how to obtain it.

---

### Phase E — Webhook story (enterprise credibility)

**Update Node webhook server (existing):**

- Add idempotency (store processed event IDs; ignore duplicates)
- Add explicit request size limit guidance
- Add rate limiting guidance
- Keep signature verification as first-class

**Add Python webhook receiver:**

- Minimal FastAPI app under `examples/python/webhook_receiver/`
- Must include signature verification stub + clear integration steps

**Add doc:**

- `docs/WEBHOOK_END_TO_END.md`

---

### Phase F — Docker + SSL reliability

- Audit example Dockerfiles (if any) and ensure `ca-certificates` is installed.
- Add doc snippet: nginx `client_max_body_size 100M` (and guidance for 800MB: object storage direct upload recommended).

---

## 5) Cross-repo alignment: integrate with `audio-trust-harness`

### Why this matters

- `sonotheia-examples` should demonstrate product integration.
- `audio-trust-harness` should demonstrate evaluation/robustness methodology.
- Together, they tell a credible “research → policy → production” story.

### Add cross-links in `sonotheia-examples`

- New doc section: “Evaluation and robustness testing”
- Link to `audio-trust-harness` and explain:
  - how to produce JSONL/CSV outputs compatible with evaluation tooling
  - how deferral policies relate to Sonotheia’s recommended_action outcomes

### Add cross-links in `audio-trust-harness`

- Add a “Using this with Sonotheia” doc section (public-safe):
  - show how to feed audit outputs into a Sonotheia review workflow
  - emphasize deferral alignment

---

## 6) Improvement Plan for `audio-trust-harness` (parallel showcase upgrades)
>
> This section is for future use and should be treated as a separate task list / future PRs.
> Do not implement changes in `audio-trust-harness` from within the `sonotheia-examples` repo.

### A) Add “Showcase Quickstart”

Create in `audio-trust-harness`:

- `Documentation/SHOWCASE_QUICKSTART.md` or `Documentation/GETTING_STARTED.md`
  - 1-command run
  - sample output excerpt
  - “what deferral means” short explanation

### B) Add “Golden Dataset” small samples

- Include a tiny set of test WAVs (or generate them) with license-safe text:
  - clean speech
  - noisy speech
  - clipped sample
  - very short sample
- Ensure README references them.

### C) Add a “Sonotheia Bridge” (optional, public-safe)

- Add a helper script that takes harness summary JSON and formats:
  - “review packet”
  - recommended SAR metadata template (NOT actual SAR submission unless API access available)

### D) Visualization (roadmap pull-in)

- Add a minimal plot generator (matplotlib) that graphs:
  - deferral rates
  - fragility distributions per indicator
- Keep optional deps behind an extras flag.

---

## 7) GitHub issues & project hygiene (optional but recommended)

- Convert `NOTES.md` questions into tracked GitHub issues or a “Known Unknowns” doc page.
- Add a “Support boundaries” section: what’s public vs requires integration engineer.

---

## 8) Deliverables checklist (what the agent must produce in `sonotheia-examples`)

### New files

- `docs/SHOWCASE_QUICKSTART.md`
- `docs/WEBHOOK_END_TO_END.md` (if webhooks enhanced)
- `examples/python/golden_path_demo.py`
- `examples/python/tests/test_golden_path_demo.py`
- `examples/typescript/src/goldenPath.ts` (or similar)
- `examples/typescript` tests for routing/parse logic (minimal acceptable)

### Updated files

- Root `README.md` (golden path above the fold)
- `examples/README.md` (golden path first)
- `docs/MFA_ENROLLMENT.md` (or an explicit “Enrollment TBD / contact us” policy)

### Acceptance gates

- Python tests pass (`pytest`)
- TypeScript build passes
- Golden path runs in mock mode
- No secret leakage
- Output contract consistent

---

## 9) Open questions the agent must resolve (or document as assumptions)

- Does a public enrollment endpoint exist? If yes: exact path + payload.
- Error schema: does it include request IDs, error codes?
- `session_id`: client-generated or server-generated?
- Webhook registration: is there an API endpoint or manual setup?
- Rate limit headers: what is exposed?

If unknown, document clearly and keep examples generic/config-driven.
