# Sonotheia Examples

> **Unified showcase repository** for the Sono Platform's commercial voice fraud mitigation capabilities

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/) (Evaluation)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-Ready-3178c6.svg)](https://www.typescriptlang.org/)

> ⚠️ **Active Development**: This repository and all components are in **active development**. Examples and frameworks are being refined, APIs may change, and features are continuously being added.

This monorepo combines two complementary showcase components for the [Sono Platform](https://github.com/doronpers/sono-platform):

- **[Integration Examples](examples/)** - Integration examples for the Sonotheia API (in active development)
- **[Evaluation Framework](evaluation/)** - Research and evaluation tool for testing acoustic indicator robustness (in active development)

---

## What's This?

This repository demonstrates the **commercial voice fraud mitigation direction** for the Sono Platform through:

1. **Production Integration** (`examples/`) - Real-world integration patterns and code examples
2. **Evaluation & Research** (`evaluation/`) - Stress-testing framework for indicator robustness

Both components work together to showcase:
- How to integrate Sono Platform in production environments
- How to evaluate and validate detection systems
- Best practices for voice fraud mitigation workflows

---

## 🚀 Golden Path Demo (Start Here)

**Run a complete end-to-end workflow in minutes—no API key required for mock mode.**

The Golden Path demo shows the complete Sonotheia workflow: deepfake detection → voice MFA verification → routing decision → optional SAR submission.

### Quick Start (Mock Mode - No API Key)

**Python:**
```bash
cd examples/python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start mock server (in one terminal)
python mock_api_server.py

# Run golden path demo (in another terminal)
python golden_path_demo.py ../test-audio/clean_tone.wav --mock
```

**TypeScript:**
```bash
cd examples/typescript
npm install && npm run build

# Start mock server (Python, in one terminal)
cd ../python && python mock_api_server.py

# Run golden path demo (in another terminal)
cd ../typescript
npm run golden-path -- ../test-audio/clean_tone.wav --mock
```

### Real API Mode (Requires API Key)

```bash
# Python
export SONOTHEIA_API_KEY=your_key
python golden_path_demo.py audio.wav

# TypeScript
export SONOTHEIA_API_KEY=your_key
npm run golden-path -- audio.wav
```

📖 **[Showcase Quickstart Guide](documentation/SHOWCASE_QUICKSTART.md)** - Complete guide with all modes and troubleshooting

---

## Governance & Interpretation (Read This First)

> ⚠️ **Important**: Outputs are suggestive signals, not identity proofs. Results should be interpreted within the context of your security workflow and used as part of a broader decision-making process.

Before integrating or evaluating, please review:

- **[Promotion Checklist](documentation/governance/PROMOTION_CHECKLIST_PUBLIC.md)** - Standards for promoting indicators to production
- **[Reason Codes Registry](documentation/governance/REASON_CODES_REGISTRY_PUBLIC.md)** - Standardized reason codes for results
- **[Evidence Logging Standard](documentation/governance/EVIDENCE_LOGGING_STANDARD_PUBLIC.md)** - Requirements for audit trails and evidence logging

📖 **[How to Interpret Results](documentation/strategy/HOW_TO_INTERPRET_RESULTS.md)** - Comprehensive guide on understanding outputs, confidence bounds, and proper usage

---

## Repository Structure

```
sonotheia-examples/
├── examples/                # Integration Examples - Production patterns
│   ├── README.md           # Integration examples documentation
│   ├── curl/               # cURL examples
│   ├── python/             # Python client examples
│   ├── typescript/         # TypeScript examples
│   └── node/               # Node.js examples
│
├── evaluation/              # Audio Trust Harness - Research framework
│   ├── README.md           # Evaluation framework documentation
│   ├── src/                # Source code
│   ├── tests/              # Test suite
│   └── config/             # Configuration files
│
└── documentation/           # Shared documentation
    ├── GETTING_STARTED.md  # Quick start guide
    └── ...
```

---

## Quick Start

**New to Sonotheia?** Start with the **[Golden Path Demo](#-golden-path-demo-start-here)** above for a complete workflow in minutes.

**First time setup?** See **[Launch & Onboarding Guide](documentation/LAUNCH_AND_ONBOARDING.md)** for cross-platform setup instructions (Windows & macOS).

**Looking for detailed guides?** See [documentation/START_HERE.md](documentation/START_HERE.md)

### For Production Integration

If you want to integrate Sono Platform into your application:

```bash
# Python example
cd examples/python
pip install -r requirements.txt
export SONOTHEIA_API_KEY=your_key
python main.py audio.wav

# TypeScript example
cd examples/typescript
npm install && npm run build
export SONOTHEIA_API_KEY=your_key
node dist/index.js audio.wav
```

📖 **[Integration Examples Guide](examples/README.md)**

### For Evaluation & Research

If you want to stress-test acoustic indicators and evaluate robustness:

```bash
cd evaluation
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
python -m audio_trust_harness run --audio test.wav --out audit.jsonl
```

📖 **[Evaluation Framework Guide](evaluation/README.md)**

---

## Components

### Integration Examples (`examples/`)

**Sonotheia Examples** - Production-ready integration examples for the Sonotheia API.

**Key Features:**
- Multi-language support (cURL, Python, TypeScript, Node.js)
- Production patterns (retry logic, rate limiting, circuit breakers)
- Evaluation tools and testing harnesses
- Comprehensive documentation

**Use Cases:**
- Voice-based multi-factor authentication (MFA)
- Synthetic speech detection
- Suspicious Activity Report (SAR) generation
- Production integration patterns

📖 **[Full Documentation](examples/README.md)**

---

### Evaluation Framework (`evaluation/`)

**Audio Trust Harness** - A research and evaluation framework for testing acoustic indicator robustness under adversarial perturbations.

**Key Features:**
- Stress-test indicators with controlled transformations
- Measure stability across perturbations
- Generate deferral signals for human review
- Produce complete audit trails

**Use Cases:**
- Research & evaluation of new indicators
- Validation of indicator stability
- Quality assurance for content moderation
- Indicator development and benchmarking

📖 **[Full Documentation](evaluation/README.md)**

---

## Architecture

Both components showcase different aspects of the Sono Platform:

```
┌─────────────────────────────────────────────────────────┐
│              Sono Platform (Production)                 │
│  https://github.com/doronpers/sono-platform            │
└─────────────────────────────────────────────────────────┘
                        ▲
                        │
        ┌────────────────┴────────────────┐
        │                                 │
┌───────▼────────┐            ┌──────────▼──────────┐
│  Integration   │            │   Evaluation        │
│  Examples       │            │   Framework        │
│                 │            │                     │
│ • API clients   │            │ • Stress-test       │
│ • MFA workflows │            │ • Robustness        │
│ • SAR generation│            │ • Validation        │
│ • Production    │            │ • Research          │
│   patterns      │            │                     │
└─────────────────┘            └─────────────────────┘
```

---

## Documentation

### Getting Started
- **[Integration Quick Start](documentation/GETTING_STARTED.md)** - 5-minute integration setup
- **[Evaluation Quick Start](evaluation/documentation/SHOWCASE_QUICKSTART.md)** - 5-minute evaluation setup

### Guides
- **[Integration Best Practices](documentation/BEST_PRACTICES.md)** - Production integration patterns
- **[Evaluation Workflows](evaluation/documentation/WORKFLOWS.md)** - Common evaluation patterns

### Reference
- **[Documentation Index](documentation/INDEX.md)** - Complete documentation navigation
- **[Evaluation API](evaluation/README.md#usage-guide)** - CLI commands and configuration

---

## Contributing

We welcome contributions. Please see:
- **[Contributing Guide](CONTRIBUTING.md)** - Guidelines for contributing to this repository
- **[Evaluation Framework Contributing](evaluation/CONTRIBUTING.md)** - Guidelines for evaluation framework

---

## License

This repository is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

> **Note:** This license applies to the showcase code and documentation. Access to the Sono Platform service requires separate authorization.

---

## How This Repository Reflects Sonotheia's Approach

This repository embodies Sonotheia's core philosophy: **attackers optimize for what sounds convincing**, not what is physically or system-consistent. **Sounding real is not the same as being physically or system-consistent**. Our goal is **measurably safer decisions—fewer exceptions, fewer bypasses, fewer successful fraud events**.

The examples and evaluation framework here demonstrate how to:
- Use acoustic indicators as signals within broader security workflows
- Apply confidence bounds and reason codes appropriately
- Leverage deferral mechanisms as a control mechanism
- Avoid prohibited uses (e.g., treating signals as identity proofs)

This aligns with Sonotheia's commitment to transparency, proper interpretation, and measurable security outcomes rather than perfect detection claims.

---

## Related Resources

- 🌐 **[Sono Platform](https://github.com/doronpers/sono-platform)** - Production platform monorepo
- 📖 **[Sono Platform Documentation](https://github.com/doronpers/sono-platform/tree/main/documentation)** - Complete platform docs
- 🎯 **[Sonotheia API](https://api.sonotheia.com)** - Production API endpoint

---

## Support

- 📧 **Email:** Contact your Sono Platform integration engineer
- 🐛 **Issues:** [Open an issue](https://github.com/doronpers/sonotheia-examples/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/doronpers/sonotheia-examples/discussions)

---

Built with ❤️ for secure voice authentication and fraud mitigation

[Integration Examples](examples/) • [Evaluation Framework](evaluation/) • [Documentation](documentation/) • [Contributing](CONTRIBUTING.md) • [License](LICENSE)
