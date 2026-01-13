# 🎙️ Sonotheia Examples

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-Ready-3178c6.svg)](https://www.typescriptlang.org/)

> **Research harness for stress-testing synthetic speech detection**: calibrated deferral, evidence-first outputs, voice MFA, and SAR workflows.

This repository provides integration examples and evaluation tools for the [Sonotheia API](https://api.sonotheia.com) — emphasizing repeatable tests, calibrated deferral, and structured review when outputs are uncertain.

---

## 📋 Table of Contents

- [What's This?](#whats-this)
- [Key Features](#-key-features)
- [Quickstart](#-quickstart)
- [Examples by Language](#-examples-by-language)
- [Output Format](#-output-format)
- [Documentation](#-documentation)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)

---

## What's This?

**Sonotheia Examples** is an **integration and evaluation reference**, not a production SDK. It helps you:

- ✅ Test synthetic speech detection with real-world audio
- ✅ Implement voice-based multi-factor authentication (MFA)
- ✅ Generate Suspicious Activity Reports (SAR) for compliance
- ✅ Evaluate model performance with calibrated deferral strategies
- ✅ Build production-ready integrations with retry logic, rate limiting, and circuit breakers

> **Note:** The production Sonotheia API is hosted at `https://api.sonotheia.com`

---

## ✨ Key Features

| Feature | Description |
| ------- | ----------- |
| 🎯 **Multi-Language Support** | cURL, Python, TypeScript, and Node.js examples |
| 🔄 **Production Patterns** | Retry logic, rate limiting, circuit breakers, webhook handlers |
| 📊 **Evaluation Tools** | Audio slicing, perturbation tests, audit-grade measurement records |
| 🔐 **Security First** | SSL/TLS best practices, secure credential handling |
| 📦 **Docker Ready** | Production-grade Dockerfiles with proper SSL certificate handling |
| 🧪 **Testing Harness** | pytest fixtures, mocking patterns, real file descriptor testing |
| 📖 **Comprehensive Docs** | FAQs, best practices, troubleshooting, API migration guides |

---

## 🚀 Quickstart

> **New here?** Check out our [Getting Started Guide](documentation/GETTING_STARTED.md) for a 5-minute walkthrough.
>
> **Know what you want to run?** Jump straight to the [Examples Overview](examples/README.md) for one-command starts across every language.

### 1. Set Up Credentials

#### Option A: Using `.env` file (recommended)

```bash
cp .env.example .env
# Edit .env and set SONOTHEIA_API_KEY=your_actual_key
```

#### Option B: Export environment variables

```bash
export SONOTHEIA_API_URL=https://api.sonotheia.com
export SONOTHEIA_API_KEY=YOUR_API_KEY

# Optional: Override endpoint paths if needed
# export SONOTHEIA_DEEPFAKE_PATH=/v1/voice/deepfake
# export SONOTHEIA_MFA_PATH=/v1/mfa/voice/verify
# export SONOTHEIA_SAR_PATH=/v1/reports/sar
```

### 2. Pick Your Language

Choose the example that fits your workflow:

- **[cURL](#curl)** - Quick one-liners for smoke tests
- **[Python](#python)** - Full-featured client with retry logic
- **[TypeScript](#typescript)** - Type-safe client with comprehensive types
- **[Node.js](#nodejs)** - Advanced patterns including batch processing and webhooks

### 3. Prepare Audio

For best results, use:

- **Format**: 16 kHz mono WAV, Opus, MP3, or FLAC
- **Duration**: 3-10 seconds optimal (up to 10 minutes supported with streaming)
- **Size**: Maximum 10 MB per file

### 4. Run an Example

```bash
# Example: Deepfake detection with cURL
./examples/curl/deepfake-detect.sh audio.wav

# Example: Python with MFA
python examples/python/main.py audio.wav --enrollment-id enroll-123
```

### 🏠 Local Development (Optional)

For local testing without requiring an API key, use the [Sono Platform](https://github.com/doronpers/sono-platform) monorepo:

```bash
# Clone and start locally
git clone https://github.com/doronpers/sono-platform.git
cd sono-platform/modes/sonotheia
./start.sh

# Point examples to local API
export SONOTHEIA_API_URL=http://localhost:8000
```

See the [Sono Platform README](https://github.com/doronpers/sono-platform#quick-start) for full setup instructions.

---

## 📂 Examples by Language

### cURL

**Minimal scripts for quick API testing**. Ideal for CI/CD smoke tests and debugging.

```bash
# Deepfake detection
./examples/curl/deepfake-detect.sh audio.wav

# Voice MFA verification
SONOTHEIA_ENROLLMENT_ID=enroll-123 ./examples/curl/mfa-verify.sh audio.wav

# SAR generation
./examples/curl/sar-report.sh session-123 review "Manual review"
```

**Requirements:** `SONOTHEIA_API_KEY` environment variable

---

### Python

**Production-ready client** with retry logic, rate limiting, and circuit breakers.

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r examples/python/requirements.txt

# Run
python examples/python/main.py audio.wav --enrollment-id enroll-123
```

**Requirements:** Python 3.9+

**Advanced features:**

- Automatic retry with exponential backoff
- Rate limiting and circuit breakers
- Streaming responses
- Kubernetes deployment manifests
- Comprehensive test suite with pytest

📖 **[Full Python Documentation](examples/python/README.md)**

---

### TypeScript

**Type-safe client** with full type definitions and compile-time validation.

```bash
# Setup
cd examples/typescript
npm install && npm run build

# Run
export SONOTHEIA_API_KEY=YOUR_API_KEY
node dist/index.js audio.wav --enrollment-id enroll-123
```

**Requirements:** Node.js 18+

**Features:**

- Complete TypeScript type definitions
- Compile-time type safety
- IDE autocomplete support
- ES modules support

---

### Node.js

**Advanced patterns** including batch processing and webhook servers.

```bash
# Batch processor
cd examples/node && npm install
export SONOTHEIA_API_KEY=YOUR_API_KEY
node batch-processor.js /path/to/*.wav

# Webhook server
PORT=3000 SONOTHEIA_WEBHOOK_SECRET=your_secret node webhook-server.js
```

**Requirements:** Node.js 18+

**Features:**

- Batch file processing
- Webhook event handling
- Async queue management
- Production monitoring patterns

📖 **[Full Node.js Documentation](examples/node/README.md)**

---

## 📊 Output Format

Example response structure (actual values vary by endpoint):

```json
{
  "deepfake": {
    "score": 0.82,
    "recommended_action": "defer_to_review",
    "latency_ms": 640
  },
  "mfa": {
    "verified": true,
    "enrollment_id": "enroll-123",
    "confidence": 0.93
  },
  "sar": {
    "status": "submitted",
    "case_id": "sar-001234"
  }
}
```

> ⚠️ **Important:** Ambiguous outcomes (e.g., `defer_to_review`) should trigger structured human review workflows.

---

## 📚 Documentation

### 📖 **[Complete Documentation Index](documentation/INDEX.md)**

Find everything organized by purpose, topic, and type.

### User Guides

| Document | Description |
| -------- | ----------- |
| [Getting Started](documentation/GETTING_STARTED.md) | 5-minute quickstart guide |
| [Use Cases](documentation/USE_CASES.md) | Real-world integration scenarios |
| [FAQ](documentation/FAQ.md) | Common questions and answers |
| [Best Practices](documentation/BEST_PRACTICES.md) | Integration patterns and recommendations |
| [Enhanced Examples](documentation/ENHANCED_EXAMPLES.md) | Advanced features (retries, streaming, monitoring) |
| [Audio Preprocessing](documentation/AUDIO_PREPROCESSING.md) | FFmpeg and SoX guide |
| [Troubleshooting](documentation/TROUBLESHOOTING.md) | Common issues and solutions |
| [MFA Enrollment Guide](documentation/MFA_ENROLLMENT.md) | Voice enrollment process |
| [Webhook Schemas](documentation/WEBHOOK_SCHEMAS.md) | Webhook event payloads |
| [API Migration Guide](documentation/API_MIGRATION_GUIDE.md) | Version update guidance |

### For Developers

| Document | Description |
| -------- | ----------- |
| [Repository Structure](documentation/REPOSITORY_STRUCTURE.md) | How this repo is organized |
| [Coding Standards](.github/CODING_STANDARDS.md) | Code style and conventions |
| [AI Development Workflow](.github/QUICK_REFERENCE.md) | AI-assisted development guide |

### For Contributors

| Document | Description |
| -------- | ----------- |
| [Contributing Guide](.github/CONTRIBUTING.md) | How to contribute |
| [Documentation Principles](documentation/DOCUMENTATION_PRINCIPLES.md) | Dieter Rams principles |
| [Design & Content Audit](documentation/DESIGN_AUDIT.md) | Documentation quality assessment and roadmap |
| [Agent Quick Reference](.github/AGENT_QUICK_REFERENCE.md) | For AI coding agents |

---

## 📌 Essential Reading (Fast Path)

- [Getting Started](documentation/GETTING_STARTED.md) — 5-minute setup
- [Documentation Index](documentation/INDEX.md) — find anything quickly
- [Examples Overview](examples/README.md) — quick-start commands for every language
- [Design & Content Audit](documentation/DESIGN_AUDIT.md) — documentation quality and roadmap

---

## 🧪 Testing

Run tests locally to verify your setup:

### Python

```bash
cd examples/python
pip install -r requirements.txt
pytest tests/ -v
```

### TypeScript

```bash
cd examples/typescript
npm install && npm run build
npm test
```

### Node.js

```bash
cd examples/node
npm install
node --check batch-processor.js
npm test
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for:

- Code of conduct
- Development workflow
- Pull request process
- Testing requirements
- Documentation standards

**Quick links:**

- [Quick Start for Contributors](CONTRIBUTING.md#tldr---quick-contributions)
- [Coding Standards](.github/CODING_STANDARDS.md)
- [AI Development Workflow](.github/QUICK_REFERENCE.md)
- [Documentation Principles](docs/DOCUMENTATION_PRINCIPLES.md)

---

## 📄 License

This repository is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

> **Important:** This license applies to the **example code and documentation** in this repository only. Access to the Sonotheia API service requires separate authorization.

For detailed information about licensing, see [License Information](documentation/LICENSE_INFO.md).

---

## 🆘 Support

### Getting Help

- 📧 **Email:** Contact your Sonotheia integration engineer
- 📖 **API Reference:** Available on request from Sonotheia team
- 🐛 **Issues:** [Open an issue](https://github.com/doronpers/sonotheia-examples/issues) for bugs or feature requests
- 💬 **Discussions:** [GitHub Discussions](https://github.com/doronpers/sonotheia-examples/discussions) for questions

### Before Reaching Out

1. Check the [FAQ](documentation/FAQ.md)
2. Review [Troubleshooting](documentation/TROUBLESHOOTING.md)
3. Search [existing issues](https://github.com/doronpers/sonotheia-examples/issues)

### Security Issues

For security vulnerabilities, please **do not** open a public issue. Email your Sonotheia integration engineer directly.

---

## 🔗 Related Resources

- 🌐 **[Sonotheia API](https://api.sonotheia.com)** - Production API endpoint
- 📦 **[Python Package](examples/python)** - Install with `pip install -r requirements.txt`
- 🎯 **[Kubernetes Examples](examples/kubernetes)** - Production deployment manifests
- 🏠 **[Sono Platform](https://github.com/doronpers/sono-platform)** - Self-hosted monorepo for local development & testing

---

---

*Built with ❤️ for secure voice authentication*

[Getting Started](documentation/GETTING_STARTED.md) • [Documentation](documentation/INDEX.md) • [Examples](examples/) • [Contributing](CONTRIBUTING.md) • [License](LICENSE)

## Agent Instructions

> **CRITICAL**: All AI agents MUST read [`AGENT_KNOWLEDGE_BASE.md`](AGENT_KNOWLEDGE_BASE.md) before performing any tasks. It contains non-negotiable Patent, Security, and Design rules.

Additional resources:

- [Agent Behavioral Standards](documentation/Governance/AGENT_BEHAVIORAL_STANDARDS.md)
- [Optimal Agent Prompt](documentation/OPTIMAL_AGENT_PROMPT.md) - Complete instructional prompt
- [Agent Prompt](documentation/AGENT_PROMPT.md) - Standard prompt with specialized variants
