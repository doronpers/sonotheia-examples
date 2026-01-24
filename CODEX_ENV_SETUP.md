# Codex Environment Setup for sonotheia-examples

Complete configuration guide for setting up a Codex development environment for `sonotheia-examples`.

## Quick Configuration

### 1. Name & Description
- **Name**: `sonotheia-examples / dev`
- **Description**: `Full sonotheia-examples dev env with dependencies, examples, and evaluation framework.`

### 2. Container Image & Workspace
- **Container image**: `universal`
- **Workspace directory**: `/workspace/sonotheia-examples` (default)

### 3. Setup Script & Caching
- **Setup script (Manual)**: `/workspace/sonotheia-examples/scripts/codex-setup.sh`
- **Container Caching**: `On`
- **Maintenance script**: `pip install -e . && pip install -e examples/python/ && pip install -e evaluation/`

### 4. Environment Variables
```
SONOTHEIA_EXAMPLES_ENV=codex
PYTHONUNBUFFERED=1
PYTHONUTF8=1
```

### 5. Secrets (API Keys)
- `OPENAI_API_KEY` - For example integrations
- `ANTHROPIC_API_KEY` - For example integrations
- `SONOTHEIA_API_KEY` - For sono-platform API (if testing integrations)

### 6. Agent Internet Access
- **Agent internet access**: `On`
- **Domain allowlist**: Start with `Common dependencies`, then add:
  - `api.openai.com`
  - `api.anthropic.com`
  - `pypi.org`
  - `files.pythonhosted.org`
  - `github.com`
- **Allowed HTTP Methods**: `All methods`

## Special Considerations

### Examples Repository
- Primarily for documentation and example code
- Less critical for automated testing
- Useful for generating new examples and documentation
