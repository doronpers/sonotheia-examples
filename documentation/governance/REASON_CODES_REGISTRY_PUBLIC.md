# Reason Codes Registry (Public)

This registry defines audit-ready reason codes for voice-channel security and workflow hardening. Codes are intended for external review, internal audits, and consistent reporting.

## Usage

- Assign **one primary code** per outcome, plus optional secondary codes.
- Codes must be recorded for **accept**, **defer**, **decline**, and **manual review** outcomes.
- Outputs are **probabilistic** and must be documented as such.

> “Treat voice like evidence: evaluate integrity + provenance, then integrate into layered controls.”

## Code format

- **Prefix**: `EVC` (Evidence / Voice / Controls)
- **Category**: `INTEGRITY`, `PROVENANCE`, `CONTEXT`, `PROCESS`, `POLICY`
- **Sequence**: 3-digit numeric

Example: `EVC-INTEGRITY-101`

## Registry

### Integrity
- `EVC-INTEGRITY-101` — Signal integrity insufficient (noise, capture artifacts, or clipping).
- `EVC-INTEGRITY-102` — Integrity inconsistent across segments (instability or sudden shifts).
- `EVC-INTEGRITY-103` — Integrity passed but confidence is low; defer to layered controls.

### Provenance
- `EVC-PROVENANCE-201` — Source provenance missing or unverifiable.
- `EVC-PROVENANCE-202` — Chain of custody unclear or evidence of tampering.
- `EVC-PROVENANCE-203` — Provenance partially verified; defer decision.

### Context
- `EVC-CONTEXT-301` — Context mismatch (policy scope, device posture, or environment invalid).
- `EVC-CONTEXT-302` — Channel conditions outside validated boundary conditions.

### Process
- `EVC-PROCESS-401` — Manual review required due to ambiguity or conflicting signals.
- `EVC-PROCESS-402` — Deferral triggered; safer workflow selected.

### Policy
- `EVC-POLICY-501` — Policy requires additional verification before action.
- `EVC-POLICY-502` — Policy decline due to unacceptable risk.

## Notes

- “Perceptual realism ≠ physical authenticity.”
- No silver bullets: layered defenses.
- Deferral is valid; it preserves safety when evidence is insufficient.
