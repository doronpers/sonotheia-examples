# Sonotheia Examples Overview

> **📦 Monorepo Notice**: This is the **Integration Examples** component of the `sonotheia-examples` monorepo.
> See [Start Here](../documentation/START_HERE.md) for the fastest path, the [root README](../README.md) for an overview of all components, or jump to [Evaluation Framework](../evaluation/README.md) for research and evaluation tools.
>
> **Quick-start commands for every implementation.** Choose your language, run the command, get results.
>
> ⚠️ **Active Development**: These integration examples are in **active development**. Examples are being refined, APIs may change, and new patterns are continuously being added.

This directory contains working examples in multiple languages demonstrating Sonotheia API integration. Each example includes proper error handling, retry logic, and security best practices.

## 🚀 Golden Path Demo (Recommended First Step)

**Run a complete end-to-end workflow in minutes.**

The Golden Path demo demonstrates the complete Sonotheia workflow: deepfake detection → voice MFA verification → routing decision → optional SAR submission.

### Quick Start

**Python (Mock Mode - No API Key):**
```bash
cd python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Terminal 1: Start mock server
python mock_api_server.py

# Terminal 2: Run golden path
python golden_path_demo.py ../test-audio/clean_tone.wav --mock
```

**TypeScript (Mock Mode):**
```bash
cd typescript
npm install && npm run build

# Terminal 1: Start mock server (from python directory)
cd ../python && python mock_api_server.py

# Terminal 2: Run golden path
cd ../typescript
npm run golden-path -- ../test-audio/clean_tone.wav --mock
```

**Real API Mode:**
```bash
# Python
export SONOTHEIA_API_KEY=your_key
python golden_path_demo.py audio.wav

# TypeScript
export SONOTHEIA_API_KEY=your_key
npm run golden-path -- audio.wav
```

📖 **[Showcase Quickstart Guide](../documentation/SHOWCASE_QUICKSTART.md)** - Complete guide with all modes, options, and troubleshooting

---

## Quick Map

| Path | Purpose | Run It Fast |
| --- | --- | --- |
| `examples/curl/` | One-liner smoke tests and CI probes | `./curl/deepfake-detect.sh audio.wav` |
| `examples/python/` | Production-grade client, streaming, health checks | `python main.py audio.wav --enrollment-id enroll-123` |
| `examples/node/` | Batch processing and webhook server patterns | `node batch-processor.js file1.wav` |
| `examples/typescript/` | Type-safe client with full typings | `npm install && npm run build && node dist/index.js audio.wav` |
| `examples/kubernetes/` | Deployment manifests and probes | `kubectl apply -f deployment.yaml` |
| `examples/terraform/aws/lambda/` | Serverless/Lambda deployment pattern | `terraform apply` (after configuring AWS credentials) |

## Prerequisites

Before running any example, please ensure you have your API key and environment set up.

Detailed instructions can be found in the [Getting Started Guide](../documentation/GETTING_STARTED.md).

**Quick Summary:**

1. **API Key**: Required (export `SONOTHEIA_API_KEY=...`)
2. **Audio File**: Test files available in `examples/test-audio/`
3. **Dependencies**: Language-specific (see individual READMEs)

> **Standardization**: All examples follow the [Example Contract](EXAMPLE_CONTRACT.md) for consistent behavior across languages.

## Choosing the Right Example

Select based on your use case:

| Use Case | Best Choice | Why |
| --- | --- | --- |
| Quick API test | **cURL** | No dependencies, fastest to run |
| Production integration | **Python** | Built-in retry logic, rate limiting, comprehensive error handling |
| Web application | **TypeScript** | Type safety, IDE support, compile-time validation |
| Batch processing | **Node.js** | Async queue management, webhook handlers |
| Container deployment | **Kubernetes** | Production manifests with health checks |
| Serverless/Lambda | **Terraform** | Infrastructure as code, AWS integration |
| Call center/IVR | **Python** (`call_center_integration.py`) | Real-time processing, routing decisions, audit trails |
| Mobile app | **Python** (`mobile_app_integration.py`) | Voice MFA, transaction authorization, account security |
| E-commerce fraud | **Python** (`ecommerce_fraud_prevention.py`) | Checkout protection, order risk assessment |
| Account recovery | **Python** (`account_recovery_flow.py`) | Password reset, account unlock, security verification |
| Event-driven | **Python** (`event_driven_integration.py`) | Message queues, microservices, async processing |

## What Each Example Provides

All examples demonstrate:

- **Deepfake Detection**: Identify synthetic voice in audio
- **Voice MFA**: Multi-factor authentication using voice biometrics
- **SAR Submission**: Generate compliance reports

### Language-Specific Features

Each implementation includes language-appropriate patterns:

- **cURL**: Minimal shell scripts for CI/CD and testing
- **Python**: Enhanced client with circuit breakers, streaming, health checks, multiple integration use cases
- **TypeScript**: Full type definitions, compile-time safety
- **Node.js**: Batch processor, webhook server, async patterns
- **Kubernetes**: Deployment, service, ingress manifests
- **Terraform**: AWS Lambda, S3, API Gateway configuration

### Integration Use Cases (Python)

The Python examples include specialized integration patterns:

- **Call Center/IVR**: Real-time fraud detection during customer service calls
- **Mobile Apps**: Voice-based authentication for iOS/Android applications
- **E-commerce**: Fraud prevention for checkout and order processing
- **Account Recovery**: Secure password reset and account unlock flows
- **Event-Driven**: Message queue integration for microservices architectures

See the [Python README](python/README.md) for detailed documentation on each integration use case.

## Getting Help

Each language directory contains:

- **README.md**: Detailed setup and usage instructions
- **Working examples**: Tested, production-ready code
- **Tests**: Unit and integration test examples (where applicable)

For general questions:

- [Start Here](../documentation/START_HERE.md): Fast onboarding for integrations
- [Main README](../README.md): Repository overview
- [Getting Started Guide](../documentation/GETTING_STARTED.md): 5-minute quickstart
- [Documentation Index](../documentation/INDEX.md): Find any documentation
- [FAQ](../documentation/FAQ.md): Common questions answered
- [Best Practices](../documentation/BEST_PRACTICES.md): Production integration guide

## Next Steps

1. **Set your API key**: `export SONOTHEIA_API_KEY=your_key_here`
2. **Choose your language**: Pick from the Quick Map above
3. **Run the example**: Use the "Run It Fast" command
4. **Read the language README**: For advanced options and patterns
5. **Explore other features**: Try MFA, SAR, webhooks, batch processing

---

**Ready to start?** Pick your language from the Quick Map above and run the command!
