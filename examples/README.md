# Sonotheia Examples Overview

> **📦 Monorepo Notice**: This is the **Integration Examples** component of the `sonotheia-examples` monorepo.
> See [Start Here](../documentation/START_HERE.md) for the fastest path, the [root README](../README.md) for an overview of all components, or jump to [Evaluation Framework](../evaluation/README.md) for research and evaluation tools.

> **Quick-start commands for every implementation.** Choose your language, run the command, get results.

> ⚠️ **Active Development**: These integration examples are in **active development**. Examples are being refined, APIs may change, and new patterns are continuously being added.

This directory contains working examples in multiple languages demonstrating Sonotheia API integration. Each example includes proper error handling, retry logic, and security best practices.

## Quick Map

| Path | Purpose | Run It Fast |
|---|---|---|
| `examples/curl/` | One-liner smoke tests and CI probes | `./curl/deepfake-detect.sh audio.wav` |
| `examples/python/` | Production-grade client, streaming, health checks | `python main.py audio.wav --enrollment-id enroll-123` |
| `examples/node/` | Batch processing and webhook server patterns | `node batch-processor.js file1.wav` |
| `examples/typescript/` | Type-safe client with full typings | `npm install && npm run build && node dist/index.js audio.wav` |
| `examples/kubernetes/` | Deployment manifests and probes | `kubectl apply -f deployment.yaml` |
| `examples/terraform/aws/lambda/` | Serverless/Lambda deployment pattern | `terraform apply` (after configuring AWS credentials) |

## Prerequisites

Before running any example, you need:

1. **API Key**: Required for all examples (contact Sonotheia support or your integration engineer to obtain one)
   ```bash
   # Option A: Using .env file (recommended)
   cp ../.env.example ../.env
   # Edit .env and set SONOTHEIA_API_KEY=your_actual_key

   # Option B: Export directly
   export SONOTHEIA_API_KEY=your_api_key_here
   ```

2. **Audio File**: For testing (optional - examples provide test audio)
   - **Recommended**: 16 kHz mono WAV, 3-10 seconds
   - **Also supported**: Opus, MP3, FLAC
   - **Test files**: Available in `examples/test-audio/`

3. **Language-Specific Dependencies**: Install as needed
   - **Python**:
     ```bash
     python -m venv .venv
     source .venv/bin/activate      # On Linux/macOS
     # .venv\Scripts\activate       # On Windows
     pip install -r requirements.txt
     ```
   - **Node.js/TypeScript**: `npm install`
   - **cURL**: No additional dependencies

## Choosing the Right Example

Select based on your use case:

| Use Case | Best Choice | Why |
|----------|-------------|-----|
| Quick API test | **cURL** | No dependencies, fastest to run |
| Production integration | **Python** | Built-in retry logic, rate limiting, comprehensive error handling |
| Web application | **TypeScript** | Type safety, IDE support, compile-time validation |
| Batch processing | **Node.js** | Async queue management, webhook handlers |
| Container deployment | **Kubernetes** | Production manifests with health checks |
| Serverless/Lambda | **Terraform** | Infrastructure as code, AWS integration |


## What Each Example Provides

All examples demonstrate:
- **Deepfake Detection**: Identify synthetic voice in audio
- **Voice MFA**: Multi-factor authentication using voice biometrics
- **SAR Submission**: Generate compliance reports

### Language-Specific Features

Each implementation includes language-appropriate patterns:

- **cURL**: Minimal shell scripts for CI/CD and testing
- **Python**: Enhanced client with circuit breakers, streaming, health checks
- **TypeScript**: Full type definitions, compile-time safety
- **Node.js**: Batch processor, webhook server, async patterns
- **Kubernetes**: Deployment, service, ingress manifests
- **Terraform**: AWS Lambda, S3, API Gateway configuration

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
