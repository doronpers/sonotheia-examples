# Monorepo Overview

This document explains how the `sonotheia-examples` monorepo is organized and how its components relate to the Sono Platform.

## Structure

```
sonotheia-examples/
├── examples/              # Integration Examples
│   ├── README.md         # Integration examples documentation
│   ├── curl/             # cURL examples
│   ├── python/           # Python client
│   ├── typescript/       # TypeScript client
│   └── node/             # Node.js examples
│
├── evaluation/            # Audio Trust Harness
│   ├── README.md         # Evaluation framework documentation
│   ├── src/              # Source code
│   ├── tests/            # Test suite
│   └── config/          # Configuration
│
└── documentation/         # Shared documentation
    ├── shared/           # This directory
    └── ...               # Component-specific docs
```

## Components

### Integration Examples (`examples/`)

**Purpose:** Production-ready integration examples for the Sonotheia API

**Key Responsibilities:**
- Provide multi-language API clients
- Demonstrate production patterns
- Show real-world use cases (MFA, SAR, deepfake detection)
- Include testing and validation tools

**Target Audience:**
- Developers integrating Sono Platform
- DevOps engineers deploying services
- Product teams building voice authentication

**Technology Stack:**
- Python 3.9+, Node.js 18+, TypeScript
- Production patterns (retries, rate limiting, circuit breakers)
- Docker, Kubernetes deployment examples

---

### Evaluation Framework (`evaluation/`)

**Purpose:** Research and evaluation tool for testing acoustic indicator robustness

**Key Responsibilities:**
- Stress-test indicators with controlled perturbations
- Measure stability and fragility metrics
- Generate deferral signals for human review
- Produce audit trails for research

**Target Audience:**
- Researchers evaluating detection systems
- Developers testing indicator robustness
- QA teams validating system stability

**Technology Stack:**
- Python 3.11+
- NumPy, SciPy, librosa for audio processing
- Typer for CLI
- Pydantic for validation

---

## Relationship to Sono Platform

```
┌─────────────────────────────────────────────────────────┐
│         Sono Platform (Production System)               │
│  https://github.com/doronpers/sono-platform            │
│                                                          │
│  • XLayer Mode - Enterprise control layer               │
│  • Sonotheia Mode - Full-featured platform              │
└─────────────────────────────────────────────────────────┘
                        ▲
                        │
                        │ Showcases
                        │
        ┌───────────────┴───────────────┐
        │                               │
┌───────▼────────┐          ┌───────────▼──────────┐
│  Integration   │          │   Evaluation          │
│  Examples       │          │   Framework            │
│                 │          │                        │
│  API Clients &  │          │  Tests & Validates     │
│  Production     │          │  Indicators             │
│  Patterns       │          │                        │
└─────────────────┘          └──────────────────────┘
```

### How They Work Together

1. **Evaluation Framework** tests and validates the indicators and methods used by Sono Platform
2. **Integration Examples** show how to use Sono Platform in production
3. Both demonstrate the **commercial voice fraud mitigation direction**

---

## Development Workflow

### Working on Integration Examples

```bash
cd examples/python
pip install -r requirements.txt
pytest tests/ -v
```

### Working on Evaluation Framework

```bash
cd evaluation
pip install -e ".[dev]"
pytest
```

### Running CI Locally

Both components have their own test suites that run in CI. See:
- [Examples CI](../.github/workflows/ci.yml)
- [Evaluation Framework](evaluation/CONTRIBUTING.md#testing)

---

## Versioning

- **Integration Examples**: Follows Sono Platform API versions
- **Evaluation Framework**: Semantic versioning (currently 0.1.0)
- **Monorepo**: Versioned as a whole, components can evolve independently

---

## Contributing

See:
- **[Root README](../README.md#contributing)** - General guidelines
- **[Examples Contributing](../CONTRIBUTING.md)** - Integration-specific
- **[Evaluation Contributing](evaluation/CONTRIBUTING.md)** - Evaluation-specific

---

For more details, see the individual component READMEs:
- [Integration Examples](../examples/README.md)
- [Evaluation Framework](../evaluation/README.md)
