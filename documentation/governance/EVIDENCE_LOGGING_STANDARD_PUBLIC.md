# Evidence Logging Standard (Public)

This standard defines what evidence may be logged for voice-channel security and workflow hardening. It is designed to be audit-ready while protecting user privacy.

## Non-negotiables

- **Explicit prohibition:** Do **not** log raw audio, base64 audio, or any reconstructable audio payloads.
- **Data minimization:** Log only what is required for auditability and system integrity.
- **Purpose limitation:** Logged data must map to a defined control, reason code, and retention policy.

## Required fields (minimum)

- **Event metadata:** timestamp, request ID, workflow ID, policy version.
- **Provenance signals:** source device class, capture path, chain of custody markers.
- **Integrity signals:** non-reconstructable feature summaries (e.g., normalized metrics, hashes, or embeddings) with versioned schema.
- **Outcome:** decision status, confidence range, and **reason codes**.

## Boundary conditions

- Outputs are **probabilistic** and must be represented as confidence ranges.
- Logging does **not** imply authenticity; it supports auditability and policy enforcement.
- “Perceptual realism ≠ physical authenticity.”

## Privacy and retention

- Retention periods must be documented and enforced.
- Access controls and audit trails are mandatory.
- Any external sharing requires explicit policy approval.

## Alignment

- Treat voice like evidence: evaluate integrity + provenance, then integrate into layered controls.
- No silver bullets: layered defenses.
- Deferral is valid when evidence is insufficient.
