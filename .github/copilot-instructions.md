# Copilot / AI Agent Instructions for Sonotheia Examples ✅

Purpose: Guide AI agents through this dual-purpose repository containing both production integration examples AND a research evaluation framework. Follow `AGENT_KNOWLEDGE_BASE.md` for patent compliance and security.

## Quick elevator (what to do first) 💡
- **Choose your track**: Integration Examples (`examples/`) OR Evaluation Framework (`evaluation/`)
- Integration: `cd examples/python && python main.py audio.wav` (after setup) — see quick map below
- Evaluation: `cd evaluation && python -m audio_trust_harness run --audio test.wav --out audit.jsonl`
- **CRITICAL**: Read `AGENT_KNOWLEDGE_BASE.md` FIRST — contains patent compliance and security rules

## Repository structure (know where you are) 🗂️
```
sonotheia-examples/
├── examples/                # Integration Examples - Production patterns
│   ├── README.md           # Integration quick map & prerequisites
│   ├── curl/               # cURL one-liners for smoke tests
│   ├── python/             # Production client with retry/health checks
│   ├── typescript/         # Type-safe client with full typings
│   ├── node/               # Batch processing & webhook patterns
│   ├── kubernetes/         # Deployment manifests & probes
│   └── terraform/          # Serverless/Lambda patterns
│
├── evaluation/              # Audio Trust Harness - Research framework
│   ├── README.md           # Evaluation methodology & philosophy
│   ├── src/                # Framework source code
│   ├── tests/              # Test suite
│   ├── config/             # Configuration examples
│   └── documentation/      # Research workflow guides
│
├── documentation/           # Shared docs (API migration, troubleshooting)
└── AGENT_KNOWLEDGE_BASE.md # Prime directives
```

**Key distinction**: `examples/` = how to integrate Sonotheia API in production. `evaluation/` = how to stress-test acoustic indicators for research.

## Project conventions and gotchas (do this, not generic advice) 🛠️
- **Patent compliance (NON-NEGOTIABLE)**: NEVER use LPC, source-filter models, glottal closure detection, or static formant values in evaluation code. Use dynamic trajectories.
- **Formatting**: Black for Python (`black .`), `snake_case` for functions/vars, `PascalCase` for classes
- **Audio format**: All examples expect **float32 mono numpy arrays at 16kHz** (evaluation framework handles preprocessing)
- **API Keys**: NEVER commit `.env` files. Use `.env.example` as template, copy to `.env` and populate `SONOTHEIA_API_KEY`
- **Examples must be runnable**: Every example in `examples/` should work with minimal setup (test audio included)
- **Evaluation is research-focused**: Parameters in `evaluation/config/` are examples for exploration, NOT production-tuned values
- **Security**: NEVER log API keys, PII, or raw audio bytes

## Commands & CI expectations (copy/paste examples) ⌨️

### Integration Examples Track
```bash
# Quick smoke test (cURL)
cd examples/curl
./deepfake-detect.sh test.wav

# Python production client
cd examples/python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SONOTHEIA_API_KEY=your_key
python main.py audio.wav --enrollment-id enroll-123

# TypeScript with type safety
cd examples/typescript
npm install && npm run build
export SONOTHEIA_API_KEY=your_key
node dist/index.js audio.wav
```

### Evaluation Framework Track
```bash
cd evaluation
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

# Run stress-test harness
python -m audio_trust_harness run --audio test.wav --out audit.jsonl

# Run test suite
pytest

# Format & lint
black src/ tests/
flake8 src/ tests/
```

## Integration points & external deps to be mindful of 🔗
- **Integration Examples**: Require valid `SONOTHEIA_API_KEY` and network access to Sonotheia API
- **Evaluation Framework**: Self-contained; uses NumPy, SciPy, librosa for audio processing
- **Test audio**: Included in `examples/test-audio/` (16kHz mono WAV recommended)
- **Config files**: Both tracks have `.env.example` files — copy and customize, NEVER commit secrets

## Track-specific guidance 🎯
- **Working on Integration Examples?** Read `examples/README.md` for language-specific patterns, error handling, and API usage
- **Working on Evaluation Framework?** Read `evaluation/README.md` for methodology, `evaluation/documentation/INTERPRETING_RESULTS.md` for result interpretation
- **Adding new language example?** Follow existing pattern: include README, error handling, retry logic, health checks, and test audio
- **Extending evaluation framework?** Follow plugin architecture in `evaluation/src/indicators/` — add custom indicators without modifying core

## Testing and PR expectations ✅
- **Integration Examples**: Test with real API key (use development endpoint if available) or mock responses
- **Evaluation Framework**: Run full test suite (`cd evaluation && pytest`) and validate against reference outputs
- Run formatters: `black .` and `flake8 .` from repo root or component directory
- Update component README when adding features or examples
- Include runnable examples with sample output in PRs

## Troubleshooting FAQ ❓
- **API key errors in examples**: Confirm `.env` exists with valid `SONOTHEIA_API_KEY`, or use `export SONOTHEIA_API_KEY=...`
- **Audio format errors**: Convert to 16kHz mono WAV using `ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav`
- **Evaluation framework import errors**: Activate venv and install with `pip install -e ".[dev]"` from `evaluation/`
- **Example won't run**: Check prerequisites in `examples/README.md` (Python 3.9+, Node 18+, test audio)
- **Patent compliance concerns**: Review `AGENT_KNOWLEDGE_BASE.md` Section 0 — evaluation code must avoid LPC/formants

## Small, concrete examples from the codebase ✂️
- Minimal cURL test: `cd examples/curl && ./deepfake-detect.sh audio.wav`
- Python client with enrollment: `python main.py audio.wav --enrollment-id john_doe --threshold 0.85`
- Evaluation stress-test: `python -m audio_trust_harness run --audio test.wav --perturbation noise --out results.jsonl`
- TypeScript type-safe client: `import { SonotheiaClient } from './client'; const client = new SonotheiaClient(apiKey);`

## Where to read more (priority order) 📚
1. `AGENT_KNOWLEDGE_BASE.md` - Prime directives (patent, security, design philosophy)
2. `README.md` - Repository overview and component selection
3. `examples/README.md` - Integration quick map and language-specific guidance (if working on examples)
4. `evaluation/README.md` - Evaluation methodology and research philosophy (if working on evaluation)
5. `documentation/GETTING_STARTED.md` - Setup and prerequisites
6. `documentation/TROUBLESHOOTING.md` - Common issues and solutions

---
**Key takeaway**: This is a DUAL-PURPOSE repository. Always identify which track you're working on (Integration or Evaluation), read its specific README, and follow its conventions. Integration examples must be production-ready; evaluation code is research-focused. Patent compliance applies to both tracks. 👋
