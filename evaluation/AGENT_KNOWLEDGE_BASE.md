# Agent Knowledge Base

Essential rules for AI agents working on Audio Trust Harness.

## Prime Directives

1. **Privacy First**: Never log raw audio, full file paths, or PII
2. **Determinism**: All perturbations must be seedable and reproducible
3. **Transparency**: Rules-based decisions only (no ML black boxes)
4. **Minimal Changes**: Make surgical, focused edits

## Before Any Task

1. Read [README.md](README.md) for project overview
2. Read [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
3. Run `pytest && ruff check src/ tests/` to verify current state

## Technical Constraints

- **Audio format**: 16kHz mono float32 numpy arrays
- **Python**: 3.11+ required
- **Line length**: 100 characters
- **Testing**: All new code must have tests
- **Validation**: Use Pydantic models for data structures

## What NOT to Do

- Add ML models without explicit approval
- Make perturbations non-deterministic
- Store raw audio in audit logs
- Log full file paths (use basename only)
- Skip tests or break existing functionality

## Architecture Reference

```
src/audio_trust_harness/
├── audio.py          # Load, slice, resample
├── perturb.py        # Deterministic perturbations
├── indicators/       # Acoustic feature extraction
├── calibrate/        # Deferral policy (rules-based)
├── audit/            # JSONL logging and summaries
└── cli.py            # Typer CLI interface
```

See [NOTES.md](NOTES.md) for design rationale.
