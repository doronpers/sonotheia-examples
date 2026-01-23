# Sonotheia Python Client

> **Production-ready Python client** with retry logic, rate limiting, circuit breakers, and comprehensive examples.

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
export SONOTHEIA_API_URL=https://api.sonotheia.com  # Optional, this is the default (API host for Sonotheia.ai)
```

**Note**: Examples read from process environment variables. They do NOT automatically load `.env` files. To use a `.env` file:
- Export variables manually: `export $(cat .env | xargs)`
- Or use a tool like `python-dotenv` in your own code
- Or simply export: `export SONOTHEIA_API_KEY=your_key_here`

## Usage

### 🚀 Golden Path Demo (Recommended First Step)

Run a complete end-to-end workflow in minutes:

```bash
# Mock mode (no API key required)
# Terminal 1: Start mock server
python mock_api_server.py

# Terminal 2: Run golden path demo
python golden_path_demo.py ../test-audio/clean_tone.wav --mock

# Real API mode
export SONOTHEIA_API_KEY=your_key
python golden_path_demo.py audio.wav

# With MFA verification
python golden_path_demo.py audio.wav --enrollment-id enroll-123

# With SAR submission
python golden_path_demo.py audio.wav --session-id session-123 --sar auto
```

The Golden Path demo demonstrates:
- Deepfake detection
- Voice MFA verification (optional)
- Routing decision based on results
- Optional SAR submission
- Standardized JSON output

📖 **[Showcase Quickstart Guide](../../documentation/SHOWCASE_QUICKSTART.md)** - Complete guide with all modes and troubleshooting

### Audio Validation

Before submitting audio to the API, validate it meets requirements:

```bash
# Validate audio file
python audio_validator.py audio.wav

# Strict mode (warnings treated as errors)
python audio_validator.py --strict audio.wav

# Auto-fix common issues
python audio_validator.py --auto-fix audio.wav

# JSON output for programmatic use
python audio_validator.py --json audio.wav
```

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

> Tip: Metadata/context payloads are normalized to JSON-safe native types, including numpy scalars/arrays.

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage (when pytest-cov is available)
pytest tests/ --cov=. --cov-report=term-missing --cov-fail-under=87

# Run linter
ruff check .

# Auto-fix linting issues
ruff check --fix .
```

**Test Coverage:**
- ✅ **178 tests passing**
- ✅ **87% coverage threshold** enforced in CI
- ✅ All core modules have comprehensive test coverage
- ✅ Shared test fixtures in `tests/conftest.py`

> Tip: Activate the local virtual environment before running tests so the in-repo modules (`client.py`,
> `client_enhanced.py`, etc.) are discovered without installing a package build step.

See [Test Coverage Guide](../../documentation/development/TEST_COVERAGE.md) for detailed test coverage information.

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

- **Python**: 3.9 or later
- **Dependencies**: See `requirements.txt`
- **Optional**: `ffmpeg` for streaming audio processing
  - **Ubuntu/Debian**: `apt-get install ffmpeg`
  - **macOS**: `brew install ffmpeg`
  - **Windows**: `choco install ffmpeg`

## Advanced Examples

### Audio Analysis with DSP Features (`audio_analysis_example.py`)

Advanced example demonstrating DSP feature extraction and analysis:

```bash
# Analyze audio with detailed DSP features
python audio_analysis_example.py audio.wav

# Extract features only (no classification)
python audio_analysis_example.py audio.wav --features-only

# With custom API URL and tenant
python audio_analysis_example.py audio.wav \
  --api-url https://api.custom.com \
  --tenant-id my-tenant
```

**Features**:
- Detailed DSP feature extraction (spectral, energy, phase)
- Voice quality indicators (HNR, jitter, shimmer)
- Formant analysis
- Risk-based routing decisions
- Configurable confidence thresholds

### Voice Integrity Routing (`voice_routing_example.py`)

Financial services routing example with risk-based decision making:

```bash
# Analyze transaction with voice integrity check
python voice_routing_example.py audio.wav \
  --customer-id CUST12345 \
  --transaction-amount 75000 \
  --destination-country US \
  --new-beneficiary

# Save audit trail
python voice_routing_example.py audio.wav \
  --customer-id CUST12345 \
  --transaction-amount 50000 \
  --save-audit audit_trail.json
```

**Features**:
- Composite risk scoring (voice + transaction context)
- Multi-factor routing decisions (ALLOW/STEP_UP/CALLBACK/ESCALATE/BLOCK)
- Configurable risk thresholds
- Additional security controls recommendation
- Complete audit trail generation
- Exit codes for workflow integration

**Routing Actions**:
- `ALLOW`: Low risk, standard processing
- `REQUIRE_STEP_UP`: Medium risk, SMS OTP required
- `REQUIRE_CALLBACK`: Medium-high risk, outbound callback needed
- `ESCALATE_TO_HUMAN`: Low confidence or high risk, manual review
- `BLOCK`: Critical risk, transaction blocked

## Integration Use Cases

### Call Center / IVR Integration (`call_center_integration.py`)

Real-time voice fraud detection for call center systems and IVR platforms:

```bash
# Basic call center integration
python call_center_integration.py audio.wav \
  --call-id CALL123 \
  --agent-id AGENT456 \
  --customer-id CUST789

# High-risk transaction with MFA
python call_center_integration.py audio.wav \
  --call-id CALL123 \
  --customer-id CUST789 \
  --enrollment-id enroll-123 \
  --transaction-amount 100000 \
  --require-mfa
```

**Features**:
- Real-time deepfake detection during live calls
- Voice MFA verification for account access
- Risk-based call routing and escalation
- Compliance logging for regulated industries
- Audit trail generation

### Mobile App Integration (`mobile_app_integration.py`)

Voice-based security for mobile applications (iOS/Android):

```bash
# Account login verification
python mobile_app_integration.py audio.wav \
  --user-id user123 \
  --enrollment-id enroll-456 \
  --operation login

# Transaction authorization
python mobile_app_integration.py audio.wav \
  --user-id user123 \
  --enrollment-id enroll-456 \
  --operation transaction \
  --transaction-id TXN789 \
  --amount 5000
```

**Features**:
- Account login with voice verification
- Transaction authorization
- Password reset with voice MFA
- High-security operations (wire transfers, account changes)
- Operation-specific risk thresholds

### E-commerce Fraud Prevention (`ecommerce_fraud_prevention.py`)

Fraud prevention for e-commerce platforms:

```bash
# Checkout fraud detection
python ecommerce_fraud_prevention.py audio.wav \
  --order-id ORD123 \
  --customer-id CUST456 \
  --order-amount 1500 \
  --payment-method credit_card

# High-value order with MFA
python ecommerce_fraud_prevention.py audio.wav \
  --order-id ORD123 \
  --customer-id CUST456 \
  --order-amount 10000 \
  --enrollment-id enroll-789 \
  --require-mfa
```

**Features**:
- Checkout fraud detection
- Account creation verification
- High-value order protection
- Guest checkout risk assessment
- Payment method risk analysis

### Account Recovery Flow (`account_recovery_flow.py`)

Account recovery and password reset with voice verification:

```bash
# Password reset with voice verification
python account_recovery_flow.py audio.wav \
  --user-id user123 \
  --enrollment-id enroll-456 \
  --recovery-type password_reset

# Account recovery
python account_recovery_flow.py audio.wav \
  --user-id user123 \
  --enrollment-id enroll-456 \
  --recovery-type account_recovery \
  --email user@example.com
```

**Features**:
- Password reset verification
- Account recovery with voice MFA
- Security question bypass with voice verification
- Account unlock after suspicious activity
- Strict security thresholds for recovery operations

### Event-Driven Integration (`event_driven_integration.py`)

Integration with event-driven architectures and message queues:

```bash
# Process event from message queue
python event_driven_integration.py \
  --event-file event.json \
  --queue-type sqs

# Simulate event processing
python event_driven_integration.py \
  --audio audio.wav \
  --event-type transaction_verification \
  --customer-id CUST123 \
  --simulate
```

**Features**:
- Microservices architecture integration
- Asynchronous processing pipelines
- Message queue integration (SQS, RabbitMQ, Kafka, Redis)
- Event sourcing patterns
- Pub/sub patterns

## Enhanced Examples

### Enhanced Client (`client_enhanced.py`)

Hardened client with retry logic, rate limiting, and circuit breaker patterns.

```python
from client_enhanced import SonotheiaClientEnhanced, CircuitBreakerConfig

# Configure circuit breaker
circuit_config = CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout=60.0,
    success_threshold=2,
)

# Initialize with enhanced features
with SonotheiaClientEnhanced(
    max_retries=3,
    rate_limit_rps=2.0,
    enable_circuit_breaker=True,
    circuit_breaker_config=circuit_config,
) as client:
    result = client.detect_deepfake("audio.wav")
```

**Features:**
- Exponential backoff retry with configurable attempts
- Token bucket rate limiting
- Circuit breaker for fault tolerance
- Connection pooling for better performance
- Automatic retry on transient failures (5xx errors)

### Enhanced CLI (`enhanced_example.py`)

```bash
# With retry and rate limiting
python enhanced_example.py audio.wav \
  --max-retries 5 \
  --rate-limit 2.0 \
  --enrollment-id enroll-123 \
  --verbose

# Disable circuit breaker
python enhanced_example.py audio.wav --disable-circuit-breaker
```

### Streaming Audio Processor (`streaming_example.py`)

Process long audio files by splitting into chunks:

```bash
# Process 30-minute audio file in 10-second chunks
python streaming_example.py long_audio.wav --chunk-duration 10

# With MFA verification for each chunk
python streaming_example.py audio.wav \
  --chunk-duration 10 \
  --enrollment-id enroll-123 \
  --session-id stream-session
```

**Features:**
- Automatic audio splitting using ffmpeg
- Memory-efficient processing of large files
- Aggregated results and statistics
- Optional SAR submission hooks (environment-specific)
- Progress tracking

**Requirements:** `ffmpeg` must be installed (`apt-get install ffmpeg`)

### Health Check and Monitoring (`health_check.py`)

Production health checks and monitoring utilities:

```bash
# Single health check (for CI/CD)
python health_check.py

# Continuous monitoring
python health_check.py --monitor --interval 60

# Prometheus metrics server
python health_check.py --prometheus-port 9090
```

**Features:**
- API connectivity validation
- Authentication verification
- Prometheus metrics export
- Kubernetes readiness/liveness probe compatible
- Continuous monitoring mode

**Metrics exported:**
- `sonotheia_api_health` - API health status (1=healthy, 0=unhealthy)
- `sonotheia_api_latency_ms` - API latency in milliseconds
- `sonotheia_api_checks_total` - Total number of health checks
- `sonotheia_api_errors_total` - Total number of errors

### Docker Support

Build and run examples in Docker:

```bash
# Build image
docker build -t sonotheia-python .

# Run basic example
docker run -e SONOTHEIA_API_KEY=xxx \
  -v $(pwd)/audio:/audio \
  sonotheia-python python main.py /audio/sample.wav

# Run enhanced example
docker run -e SONOTHEIA_API_KEY=xxx \
  -v $(pwd)/audio:/audio \
  sonotheia-python python enhanced_example.py /audio/sample.wav --max-retries 5

# Run streaming processor
docker run -e SONOTHEIA_API_KEY=xxx \
  -v $(pwd)/audio:/audio \
  sonotheia-python python streaming_example.py /audio/long.wav
```

Or use Docker Compose:

```bash
# Run all examples
docker-compose up

# Run specific service
docker-compose up sonotheia-enhanced
```

## Development

To contribute or modify:

1. Install dev dependencies: `pip install -r requirements.txt`
2. Make changes
3. Run tests: `pytest tests/`
4. Run linter: `ruff check .`
5. Format code: `ruff format .`

## 📌 Quick Links

- [Getting Started Guide](../../documentation/GETTING_STARTED.md) — 5-minute setup
- [Documentation Index](../../documentation/INDEX.md) — find anything quickly
- [Examples Overview](../README.md) — quick-start commands for every language
- [FAQ](../../documentation/FAQ.md) — common questions and troubleshooting
- [Best Practices](../../documentation/BEST_PRACTICES.md) — production integration guidelines
