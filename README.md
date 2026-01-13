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
- **[Integration Quick Start](examples/documentation/GETTING_STARTED.md)** - 5-minute integration setup
- **[Evaluation Quick Start](evaluation/documentation/SHOWCASE_QUICKSTART.md)** - 5-minute evaluation setup

### Guides
- **[Integration Best Practices](examples/documentation/BEST_PRACTICES.md)** - Production integration patterns
- **[Evaluation Workflows](evaluation/documentation/WORKFLOWS.md)** - Common evaluation patterns

### Reference
- **[Integration API](examples/documentation/INDEX.md)** - Complete API reference
- **[Evaluation API](evaluation/README.md#usage-guide)** - CLI commands and configuration

---

## Contributing

We welcome contributions. Please see:
- **[Integration Examples Contributing](examples/.github/CONTRIBUTING.md)** - Guidelines for integration examples
- **[Evaluation Framework Contributing](evaluation/CONTRIBUTING.md)** - Guidelines for evaluation framework

---

## License

This repository is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

> **Note:** This license applies to the showcase code and documentation. Access to the Sono Platform service requires separate authorization.

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
