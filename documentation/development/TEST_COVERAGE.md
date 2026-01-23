# Test Coverage Guide

> **Current Status**: 178 tests passing, 87% coverage threshold enforced in CI

This guide covers test coverage for the Sonotheia Python examples, including how to run tests, understand coverage reports, and maintain the 87% coverage threshold.

---

## Quick Start

### Run All Tests

```bash
cd examples/python
pytest tests/ -v
```

### Run Tests with Coverage

```bash
# When pytest-cov is available (CI environment)
pytest tests/ --cov=. --cov-report=term-missing --cov-report=html --cov-fail-under=87
```

### Current Test Status

- **213 tests passing** ✅ (up from 178)
- **53 tests skipped** (intentional - conditional tests)
- **28 tests failing** ⚠️ (need fixes - mostly enhanced_example and cleanup tests)
- **0 test errors** ✅
- **Coverage threshold**: 87% (enforced in CI)

---

## Test Infrastructure

### Shared Fixtures (`tests/conftest.py`)

All tests use shared fixtures for consistency:

- **`mock_server`** - Mock API server fixture (starts/stops automatically)
- **`test_audio`** - Test audio file creation (auto-cleanup)
- **`client`** - Pre-configured SonotheiaClient instance

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_client.py           # Basic client tests (enhanced)
├── test_client_enhanced.py # Enhanced client tests
├── test_constants.py        # Constants module tests
├── test_utils.py            # Utils module tests
├── test_response_validator.py # Response validation tests
├── test_config_validator.py   # Config validation tests
├── test_audio_validator.py    # Audio validation tests
├── test_health_check.py       # Health check tests
├── test_main.py               # CLI tests
├── test_mock_api_server.py    # Mock server tests
├── test_integration.py        # Integration tests
└── test_example_validation.py # Example validation tests
```

---

## Coverage Goals

### Module Coverage Targets

| Module | Target | Status |
|--------|--------|--------|
| `constants.py` | 100% | ✅ Complete |
| `utils.py` | 90%+ | ✅ Complete |
| `response_validator.py` | 87%+ | ✅ Complete |
| `config_validator.py` | 87%+ | ✅ Complete |
| `client.py` | 87%+ | ✅ Enhanced |
| `client_enhanced.py` | 87%+ | ✅ Enhanced |
| `audio_validator.py` | 87%+ | ✅ Complete |
| `health_check.py` | 87%+ | ✅ Complete |
| `mock_api_server.py` | 87%+ | ✅ Complete |
| `main.py` | 60%+ | ✅ Complete |
| `streaming_example.py` | 60%+ | ✅ New |
| `enhanced_example.py` | 50%+ | ⚠️ New (some failures) |
| `webhook_receiver/app.py` | 70%+ | ✅ New |
| `audio_analysis_example.py` | 65%+ | ✅ New |
| `voice_routing_example.py` | 60%+ | ✅ New |
| `load_test.py` | 40%+ | ✅ New |
| `api_types.py` | 100% | ✅ New |
| **Overall** | **87%** | **✅ Enforced in CI** |

---

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_client.py -v

# Run specific test
pytest tests/test_client.py::TestSonotheiaClient::test_init_with_api_key -v
```

### Coverage Reporting

Coverage reporting requires `pytest-cov` which is available in CI. To run locally:

```bash
# Install pytest-cov (if available)
pip install pytest-cov

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing --cov-report=html

# With threshold enforcement
pytest tests/ --cov=. --cov-fail-under=87
```

### CI/CD Integration

The CI workflow (`.github/workflows/python-ci.yml`) automatically:
- Runs all tests on Python 3.9, 3.10, 3.11, 3.12
- Generates coverage reports for Python 3.11
- **Enforces 87% coverage threshold** - builds fail if coverage < 87%
- Uploads coverage reports as artifacts

---

## Test Categories

### Unit Tests

- **test_client.py** - Basic API client functionality
- **test_client_enhanced.py** - Enhanced client (retry, rate limiting, circuit breaker)
- **test_constants.py** - Shared constants
- **test_utils.py** - Utility functions
- **test_response_validator.py** - Response validation
- **test_config_validator.py** - Configuration validation
- **test_audio_validator.py** - Audio file validation
- **test_health_check.py** - Health check functionality
- **test_main.py** - CLI interface
- **test_mock_api_server.py** - Mock API server

### Integration Tests

- **test_integration.py** - End-to-end tests with mock server
- **test_example_validation.py** - Example script validation

### Example Script Tests

- **test_streaming_example.py** - Streaming audio processor
- **test_enhanced_example.py** - Enhanced CLI example
- **test_audio_analysis_example.py** - Audio analysis with DSP features
- **test_voice_routing_example.py** - Voice integrity routing
- **test_webhook_receiver.py** - FastAPI webhook receiver
- **test_load_test.py** - Load testing utilities
- **test_api_types.py** - Type definition verification

---

## Writing New Tests

### Test Structure

```python
import pytest
from client import SonotheiaClient

class TestNewFeature:
    """Tests for new feature."""
    
    def test_feature_success(self):
        """Test successful feature execution."""
        client = SonotheiaClient(api_key="test-key")
        # Test implementation
        assert result == expected
```

### Using Shared Fixtures

```python
def test_with_mock_server(client, test_audio):
    """Test using shared fixtures."""
    result = client.detect_deepfake(test_audio)
    assert "score" in result
```

### Coverage Requirements

- New code must maintain 87% overall coverage
- Core modules must maintain 87%+ coverage
- Utility modules must maintain 87%+ coverage
- Example scripts target 60%+ coverage

---

## Troubleshooting

### Tests Fail with "unrecognized arguments: --cov"

**Problem**: `pytest-cov` not installed

**Solution**: Coverage is enforced in CI. For local testing, run without coverage:
```bash
pytest tests/ -v
```

### Mock Server Fails to Start

**Problem**: Flask not available or port conflict

**Solution**: 
- Install Flask: `pip install flask`
- Check port availability (default: 8914)
- Review test logs for specific error

### Coverage Below Threshold

**Problem**: New code added without tests

**Solution**:
1. Identify uncovered lines: `pytest tests/ --cov=. --cov-report=term-missing`
2. Add tests for uncovered code
3. Ensure all edge cases and error paths are tested

---

## Historical Context

For detailed implementation history, see:
- `documentation/Archive/Reports-Historical/TEST_COVERAGE_IMPLEMENTATION_SUMMARY.md`
- `documentation/Archive/Reports-Historical/TEST_COVERAGE_ASSESSMENT.md`
- `documentation/Archive/Reports-Historical/TEST_COVERAGE_QUICK_START.md`

---

## Related Documentation

- [Contributing Guide](../CONTRIBUTING.md) - Contribution guidelines including testing
- [Python README](../../examples/python/README.md) - Python examples documentation
- [CI Workflow](../../.github/workflows/python-ci.yml) - CI/CD configuration

---

**Last Updated**: 2026-01-23  
**Recent Updates**: Added 7 new test files (61 new tests) for previously untested modules
