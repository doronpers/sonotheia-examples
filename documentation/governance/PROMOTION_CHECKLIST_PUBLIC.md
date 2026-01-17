# Promotion Checklist (Public)

This checklist defines the minimum bar for promoting voice-channel security controls into broader use. It reflects Sonotheia’s discipline: evidence-first interpretation, no silver bullets, deferral is valid, audit-ready reason codes, and no raw audio logging.

> “Perceptual realism ≠ physical authenticity.”

## Core principles

- **Evidence-first interpretation.** Treat voice like evidence: evaluate integrity + provenance, then integrate into layered controls.
- **No silver bullets: layered defenses.** Each control must fit into a multi-layer risk program (human review, device posture, network signals, policy enforcement).
- **Deferral is valid.** If evidence is weak or ambiguous, the system should defer to safer workflows rather than forcing a decision.
- **Audit-ready reason codes.** Every decision or deferral must map to a standardized reason code.
- **No raw audio logging.** Raw audio, base64 audio, and reconstructable audio payloads are prohibited in logs or analytics.

## Boundary conditions

- Outputs are **probabilistic**, not deterministic. Confidence should be communicated as a range and not a guarantee.
- Controls are **channel-specific** and **context-limited**; do not generalize beyond validated conditions.
- Operational constraints (network quality, capture devices, environment noise) can affect signal integrity.

## Promotion gates

### 1) Evidence capture & provenance
- [ ] Provenance metadata is captured (source, chain of custody, capture method, tamper indicators).
- [ ] Integrity checks are defined and validated against known-good and adversarial samples.
- [ ] Output explicitly separates *signal integrity* from *identity claims*.

### 2) Logging & privacy
- [ ] Logging adheres to the **Evidence Logging Standard** (public) and prohibits raw/base64 audio.
- [ ] Logs are minimized, structured, and auditable.

### 3) Reason codes
- [ ] All outcomes are mapped to the public **Reason Codes Registry**.
- [ ] Deferrals and manual reviews have explicit codes and triggers.

### 4) Layered controls
- [ ] Control is integrated into a broader workflow (e.g., step-up verification, policy-based gating, or human review).
- [ ] Fallback paths are defined when evidence is insufficient.

### 5) Evaluation & constraints
- [ ] Evaluation reflects real-world conditions and documented boundary constraints.
- [ ] Known failure modes and limitations are published.

## Decision outcomes

- **Promote** only when the control meets all gates with documented evidence.
- **Defer** if evidence is insufficient or boundary conditions are not met.
- **Decline** if the control introduces unacceptable risk or cannot be audited.
