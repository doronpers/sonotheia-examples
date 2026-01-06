# Sonotheia Examples Overview

> Minimal, precise directions for every example family.

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

- **API key**: `SONOTHEIA_API_KEY` must be set for every example (copy `.env.example` at repo root to `.env` and export it, or export the variables directly).
- **API host**: Defaults to `https://api.sonotheia.com`; override with `SONOTHEIA_API_URL` if needed.
- **Audio**: Prefer 16 kHz mono WAV/Opus under 10 seconds for fastest responses.

## Choosing the Right Track

- **Smoke tests / CI** → cURL scripts.
- **Production integration** → Python (retry + rate limiting baked in).
- **JavaScript ecosystem** → Node.js for operational patterns, TypeScript for typings and IDE guidance.
- **Async callbacks** → Node.js webhook server example.
- **Cloud native** → Kubernetes manifests or Terraform AWS Lambda sample.

## Signals of Readiness

- Each folder has its own README with deeper setup.
- Scripts fail fast on missing configuration.
- Commands above run without additional flags once dependencies are installed.

## Next Steps

1. Export `SONOTHEIA_API_KEY`.
2. Pick the example path above and run the “Run It Fast” command.
3. Review the language-specific README for advanced switches, retries, and observability hooks.

## 📌 Essential Reading (Fast Path)

- [Getting Started](../docs/GETTING_STARTED.md) — 5-minute setup
- [Documentation Index](../docs/INDEX.md) — find anything quickly
- [Examples Overview](README.md) — one-command runs for every track
- [Design & Content Audit](../docs/DESIGN_AUDIT.md) — current quality posture
