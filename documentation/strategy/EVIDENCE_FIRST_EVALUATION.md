# Evidence-First Evaluation (Public)

This document describes Sonotheia’s evaluation approach for voice-channel security and workflow hardening. The core idea is to treat voice as evidence, not as a single-point identity claim.

## Principles

- **Evidence-first interpretation.** Treat voice like evidence: evaluate integrity + provenance, then integrate into layered controls.
- **No silver bullets: layered defenses.** Voice-channel controls are only one layer of a broader security workflow.
- **Deferral is valid.** When evidence is weak or ambiguous, defer to safer workflows or manual review.
- **Audit-ready outputs.** Decisions are tied to standardized reason codes for transparency.

> “Perceptual realism ≠ physical authenticity.”

## Boundary conditions

- Outputs are **probabilistic** and must be communicated with confidence ranges.
- Validity is limited to documented conditions (devices, environments, capture paths).
- Performance can degrade under adverse channel conditions.

## Evaluation flow

1. **Provenance assessment**
   - Verify source, chain of custody, and capture path.
2. **Integrity assessment**
   - Evaluate signal stability and non-reconstructable features.
3. **Context check**
   - Validate policy scope, device posture, and environment constraints.
4. **Decision + reason codes**
   - Accept, defer, or decline with auditable codes.
5. **Layered integration**
   - Apply step-up verification or human review if needed.

## Logging and privacy

- Raw audio/base64 logging is explicitly prohibited.
- Logs are minimized, structured, and aligned with the Evidence Logging Standard.

## Anti-fragility and learning

- Record boundary-condition breaches and failure modes to improve controls.
- Regularly revalidate models and workflows as environments change.
