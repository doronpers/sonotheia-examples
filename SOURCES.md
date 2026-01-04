# SOURCES (for agent)

## Available repos / folders in workspace
This repository (sonotheia-examples) contains all example code directly:
- `/examples/curl/` - Bash scripts for curl examples
- `/examples/python/` - Python client implementation
- `/examples/typescript/` - TypeScript client with full type definitions
- `/examples/node/` - Node.js advanced examples (batch processor, webhook server)
- `/docs/` - Documentation (FAQ, Best Practices)

## Specific files to reuse/adapt
All code in this repository is original and created specifically for this examples repository. No external sources were adapted.

### API schemas / OpenAPI
- No formal OpenAPI specification is included yet
- API request/response schemas are inferred from working code in examples
- See NOTES.md for documented assumptions about API contracts

### Existing curl scripts
- `examples/curl/deepfake-detect.sh` - Deepfake detection
- `examples/curl/mfa-verify.sh` - MFA verification  
- `examples/curl/sar-report.sh` - SAR submission

### Existing python client code
- `examples/python/main.py` - Complete Python client with CLI interface
- `examples/python/requirements.txt` - Python dependencies

### TypeScript client code
- `examples/typescript/src/index.ts` - Type-safe TypeScript client
- `examples/typescript/package.json` - TypeScript dependencies
- `examples/typescript/tsconfig.json` - TypeScript configuration

### Node examples (webhook, batch)
- `examples/node/batch-processor.js` - Concurrent batch processing
- `examples/node/webhook-server.js` - Webhook receiver example
- `examples/node/package.json` - Node.js dependencies

## Constraints
- Do not copy any proprietary customer data.
- Never commit real API keys or secrets to version control.
- All examples use environment variables for configuration.
- API endpoint paths and schemas are assumptions based on working examples.
- For missing information, see NOTES.md "Questions for Doron" section.
