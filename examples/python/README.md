# Sonotheia Python Client

Python client library and CLI for the Sonotheia voice fraud detection API.

## Installation

```bash
# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Set your API credentials as environment variables:

```bash
export SONOTHEIA_API_KEY=your_api_key_here
export SONOTHEIA_API_URL=https://api.sonotheia.com  # Optional, this is the default
```

Or copy the top-level `.env.example` to `.env` and fill in your credentials.

## Usage

### Command Line Interface

The `main.py` script provides a simple CLI for testing the API:

```bash
# Basic deepfake detection
python main.py path/to/audio.wav

# With MFA verification (requires enrollment ID)
python main.py path/to/audio.wav --enrollment-id enroll-123

# With SAR submission
python main.py path/to/audio.wav --session-id session-123

# Complete workflow
python main.py audio.wav \
  --enrollment-id enroll-123 \
  --session-id session-123 \
  --decision review \
  --reason "Suspicious activity detected"
```

### As a Library

You can also use the `SonotheiaClient` class in your own Python code:

```python
from client import SonotheiaClient

# Initialize client
client = SonotheiaClient(api_key="your_key_here")

# Detect deepfake
result = client.detect_deepfake("audio.wav", metadata={"session_id": "my-session"})
print(f"Deepfake score: {result['score']}")

# Verify MFA
mfa_result = client.verify_mfa("audio.wav", "enroll-123", context={"channel": "ivr"})
print(f"Verified: {mfa_result['verified']}")

# Submit SAR
sar_result = client.submit_sar("session-123", "review", "High risk detected")
print(f"Case ID: {sar_result['case_id']}")
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing

# Run linter
ruff check .

# Auto-fix linting issues
ruff check --fix .
```

## API Client Reference

### `SonotheiaClient`

Main client class for interacting with the Sonotheia API.

**Constructor parameters:**
- `api_key` (str | None): API key for authentication
- `api_url` (str | None): Base API URL
- `deepfake_path` (str | None): Deepfake endpoint path
- `mfa_path` (str | None): MFA endpoint path
- `sar_path` (str | None): SAR endpoint path
- `timeout` (int): Request timeout in seconds (default: 30)

**Methods:**

#### `detect_deepfake(audio_path: str, metadata: dict | None = None) -> dict`

Detect if audio contains a deepfake.

**Parameters:**
- `audio_path`: Path to audio file (WAV, Opus, MP3, or FLAC)
- `metadata`: Optional metadata dictionary

**Returns:** Dict with keys `score`, `label`, `latency_ms`, `session_id` (optional)

#### `verify_mfa(audio_path: str, enrollment_id: str, context: dict | None = None) -> dict`

Verify caller identity via voice MFA.

**Parameters:**
- `audio_path`: Path to audio file
- `enrollment_id`: Enrollment/voiceprint identifier
- `context`: Optional context dictionary

**Returns:** Dict with keys `verified`, `enrollment_id`, `confidence`, `session_id` (optional)

#### `submit_sar(session_id: str, decision: str, reason: str, metadata: dict | None = None) -> dict`

Submit a Suspicious Activity Report.

**Parameters:**
- `session_id`: Session identifier
- `decision`: Decision type - 'allow', 'deny', or 'review'
- `reason`: Human-readable reason
- `metadata`: Optional metadata dictionary

**Returns:** Dict with keys `status`, `case_id`, `session_id`

## Error Handling

All methods raise `requests.HTTPError` on API errors and `requests.RequestException` for network issues:

```python
import requests
from client import SonotheiaClient

client = SonotheiaClient()

try:
    result = client.detect_deepfake("audio.wav")
except requests.HTTPError as e:
    print(f"API error: {e.response.status_code} - {e.response.text}")
except requests.RequestException as e:
    print(f"Network error: {e}")
```

## Requirements

- Python 3.9 or later
- See `requirements.txt` for dependencies

## Development

To contribute or modify:

1. Install dev dependencies: `pip install -r requirements.txt`
2. Make changes
3. Run tests: `pytest tests/`
4. Run linter: `ruff check .`
5. Format code: `ruff format .`

## See Also

- [FAQ](../../docs/FAQ.md) - Common questions and troubleshooting
- [Best Practices](../../docs/BEST_PRACTICES.md) - Integration guidelines
- [NOTES.md](../../NOTES.md) - Assumptions and open questions
