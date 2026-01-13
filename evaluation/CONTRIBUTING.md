# Contributing to Audio Trust Harness

> **For AI Agents**: Read [AGENT_KNOWLEDGE_BASE.md](AGENT_KNOWLEDGE_BASE.md) first.

## Project Structure

```
src/audio_trust_harness/
├── audio.py              # Audio loading, slicing, resampling
├── perturb.py            # Perturbation implementations
├── indicators/           # Acoustic indicators (spectral, temporal)
├── calibrate/policy.py   # Deferral decision logic
├── audit/                # JSONL record generation, summaries
└── cli.py                # Typer-based CLI

tests/                    # Pytest test suite
```

## Development Setup

```bash
pip install -e ".[dev]"
pytest                    # Verify baseline
ruff check src/ tests/    # Check style
```

## Code Conventions

| Category | Convention |
|----------|-----------|
| Line length | 100 characters |
| Python | 3.11+ |
| Classes | `PascalCase` |
| Functions | `snake_case` |
| Constants | `UPPER_SNAKE_CASE` |

**Testing**: All new features need tests. Use seeds for determinism.

**Perturbations**: Must be deterministic, implement `Perturbation` base class, provide `get_params()`.

**Indicators**: Must implement `BaseIndicator`, return `dict[str, float]` from `compute()`.

## Common Tasks

### Adding a Perturbation
1. Create class in `perturb.py` inheriting from `Perturbation`
2. Implement `apply(audio, sample_rate)` and `get_params()`
3. Add to `get_perturbation()` factory
4. Add tests in `tests/test_perturb.py`

### Adding an Indicator
1. Create class in `indicators/` inheriting from `BaseIndicator`
2. Implement `compute(audio, sample_rate)` returning dict
3. Add tests in `tests/test_indicators.py`

### Modifying Deferral Policy
1. Edit `calibrate/policy.py`
2. Add tests in `tests/test_policy.py`
3. Document rationale in NOTES.md

## Validation

```bash
ruff format src/ tests/   # Format
ruff check src/ tests/    # Lint
pytest --cov              # Test with coverage
```

## Security & Privacy

- Never log full file paths (only basenames)
- Never store raw audio in audit logs
- All perturbations must be deterministic
- Validate all user inputs

## Pull Request Process

1. Fork and clone the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make minimal, focused changes
4. Add tests for new functionality
5. Run validation commands above
6. Update documentation if user-facing
7. Open a pull request with clear description

## Questions?

Open an issue on GitHub for feature requests, bug reports, or design discussions.
