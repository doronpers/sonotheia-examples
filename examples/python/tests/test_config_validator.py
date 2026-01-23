"""
Tests for config_validator module.

This module tests the configuration validation functionality.
"""

from __future__ import annotations

import pytest

from config_validator import (
    APIConfig,
    ConfigValidationError,
    check_ffmpeg_installed,
    collect_issues,
    validate_api_config,
    validate_path,
    validate_required_env,
    validate_timeout,
    validate_url,
)


class TestValidateRequiredEnv:
    """Tests for validate_required_env function."""

    def test_validate_api_key_present(self, monkeypatch):
        """Test validation succeeds when API key is present."""
        monkeypatch.setenv("SONOTHEIA_API_KEY", "test-key-123")
        result = validate_required_env("SONOTHEIA_API_KEY")
        assert result == "test-key-123"

    def test_validate_api_key_missing(self, monkeypatch):
        """Test validation fails when API key is missing."""
        monkeypatch.delenv("SONOTHEIA_API_KEY", raising=False)
        with pytest.raises(ConfigValidationError, match="Required environment variable"):
            validate_required_env("SONOTHEIA_API_KEY")

    def test_validate_with_default(self, monkeypatch):
        """Test validation succeeds with default value."""
        monkeypatch.delenv("TEST_VAR", raising=False)
        result = validate_required_env("TEST_VAR", default="default-value")
        assert result == "default-value"


class TestValidateURL:
    """Tests for validate_url function."""

    def test_validate_api_url_format_valid_https(self):
        """Test validation succeeds with valid HTTPS URL."""
        result = validate_url("https://api.example.com")
        assert result == "https://api.example.com"

    def test_validate_api_url_format_valid_http(self):
        """Test validation succeeds with valid HTTP URL."""
        result = validate_url("http://localhost:8000")
        assert result == "http://localhost:8000"

    def test_validate_api_url_strips_trailing_slash(self):
        """Test that trailing slash is stripped."""
        result = validate_url("https://api.example.com/")
        assert result == "https://api.example.com"

    def test_validate_api_url_empty(self):
        """Test validation fails with empty URL."""
        with pytest.raises(ConfigValidationError, match="cannot be empty"):
            validate_url("")

    def test_validate_api_url_invalid_scheme(self):
        """Test validation fails with invalid scheme."""
        with pytest.raises(ConfigValidationError, match="must start with http:// or https://"):
            validate_url("ftp://example.com")

    def test_validate_api_url_no_scheme(self):
        """Test validation fails without scheme."""
        with pytest.raises(ConfigValidationError, match="must start with http:// or https://"):
            validate_url("api.example.com")


class TestValidatePath:
    """Tests for validate_path function."""

    def test_validate_paths_format_valid(self):
        """Test validation succeeds with valid path."""
        result = validate_path("/v1/voice/deepfake")
        assert result == "/v1/voice/deepfake"

    def test_validate_path_adds_leading_slash(self):
        """Test that leading slash is added if missing."""
        result = validate_path("v1/voice/deepfake")
        assert result == "/v1/voice/deepfake"

    def test_validate_path_empty(self):
        """Test validation fails with empty path."""
        with pytest.raises(ConfigValidationError, match="cannot be empty"):
            validate_path("")


class TestValidateTimeout:
    """Tests for validate_timeout function."""

    def test_validate_timeout_range_valid(self):
        """Test validation succeeds with valid timeout."""
        assert validate_timeout(30) == 30
        assert validate_timeout("30") == 30
        assert validate_timeout(1) == 1
        assert validate_timeout(300) == 300

    def test_validate_timeout_zero(self):
        """Test validation fails with zero timeout."""
        with pytest.raises(ConfigValidationError, match="must be greater than 0"):
            validate_timeout(0)

    def test_validate_timeout_negative(self):
        """Test validation fails with negative timeout."""
        with pytest.raises(ConfigValidationError, match="must be greater than 0"):
            validate_timeout(-10)

    def test_validate_timeout_too_large(self):
        """Test validation fails with timeout exceeding maximum."""
        with pytest.raises(ConfigValidationError, match="should not exceed 300 seconds"):
            validate_timeout(301)

    def test_validate_timeout_invalid_type(self):
        """Test validation fails with invalid type."""
        with pytest.raises(ConfigValidationError, match="must be a valid integer"):
            validate_timeout("invalid")


class TestValidateAPIConfig:
    """Tests for validate_api_config function."""

    def test_comprehensive_config_validation_success(self, monkeypatch):
        """Test comprehensive config validation with all parameters."""
        # Clear env vars to ensure parameters are used
        monkeypatch.delenv("SONOTHEIA_API_KEY", raising=False)
        monkeypatch.delenv("SONOTHEIA_API_URL", raising=False)
        monkeypatch.delenv("SONOTHEIA_DEEPFAKE_PATH", raising=False)
        monkeypatch.delenv("SONOTHEIA_MFA_PATH", raising=False)
        monkeypatch.delenv("SONOTHEIA_SAR_PATH", raising=False)
        monkeypatch.delenv("SONOTHEIA_TIMEOUT", raising=False)

        config = validate_api_config(
            api_key="custom-key",
            api_url="https://custom.api.com",
            deepfake_path="/custom/deepfake",
            mfa_path="/custom/mfa",
            sar_path="/custom/sar",
            timeout=60,
        )

        assert config.api_key == "custom-key"
        assert config.api_url == "https://custom.api.com"
        assert config.deepfake_path == "/custom/deepfake"
        assert config.mfa_path == "/custom/mfa"
        assert config.sar_path == "/custom/sar"
        assert config.timeout == 60

    def test_validate_api_config_from_env(self, monkeypatch):
        """Test config validation reads from environment variables."""
        monkeypatch.setenv("SONOTHEIA_API_KEY", "env-key")
        monkeypatch.setenv("SONOTHEIA_API_URL", "https://env.api.com")
        monkeypatch.setenv("SONOTHEIA_DEEPFAKE_PATH", "/env/deepfake")
        monkeypatch.setenv("SONOTHEIA_MFA_PATH", "/env/mfa")
        monkeypatch.setenv("SONOTHEIA_SAR_PATH", "/env/sar")
        monkeypatch.setenv("SONOTHEIA_TIMEOUT", "45")

        config = validate_api_config()

        assert config.api_key == "env-key"
        assert config.api_url == "https://env.api.com"
        assert config.deepfake_path == "/env/deepfake"
        assert config.mfa_path == "/env/mfa"
        assert config.sar_path == "/env/sar"
        assert config.timeout == 45

    def test_validate_api_config_defaults(self, monkeypatch):
        """Test config validation uses defaults when not provided."""
        monkeypatch.setenv("SONOTHEIA_API_KEY", "test-key")
        monkeypatch.delenv("SONOTHEIA_API_URL", raising=False)
        monkeypatch.delenv("SONOTHEIA_DEEPFAKE_PATH", raising=False)
        monkeypatch.delenv("SONOTHEIA_MFA_PATH", raising=False)
        monkeypatch.delenv("SONOTHEIA_SAR_PATH", raising=False)
        monkeypatch.delenv("SONOTHEIA_TIMEOUT", raising=False)

        config = validate_api_config()

        assert config.api_url == "https://api.sonotheia.com"
        assert config.deepfake_path == "/v1/voice/deepfake"
        assert config.mfa_path == "/v1/mfa/voice/verify"
        assert config.sar_path == "/v1/reports/sar"
        assert config.timeout == 30

    def test_validate_api_config_missing_api_key(self, monkeypatch):
        """Test config validation fails when API key is missing."""
        monkeypatch.delenv("SONOTHEIA_API_KEY", raising=False)
        with pytest.raises(ConfigValidationError, match="Required environment variable"):
            validate_api_config()


class TestCollectIssues:
    """Tests for collect_issues function."""

    def test_collect_issues_missing_api_key(self, monkeypatch, tmp_path):
        """Test that missing API key is detected."""
        monkeypatch.delenv("SONOTHEIA_API_KEY", raising=False)
        issues = collect_issues(tmp_path)

        missing_key_issues = [i for i in issues if i.code == "MISSING_API_KEY"]
        assert len(missing_key_issues) > 0
        assert missing_key_issues[0].severity == "error"

    def test_collect_issues_placeholder_api_key(self, monkeypatch, tmp_path):
        """Test that placeholder API key is detected."""
        monkeypatch.setenv("SONOTHEIA_API_KEY", "your_api_key_here")
        issues = collect_issues(tmp_path)

        placeholder_issues = [i for i in issues if i.code == "PLACEHOLDER_API_KEY"]
        assert len(placeholder_issues) > 0

    def test_collect_issues_insecure_url(self, monkeypatch, tmp_path):
        """Test that insecure HTTP URL is detected."""
        monkeypatch.setenv("SONOTHEIA_API_URL", "http://api.example.com")
        issues = collect_issues(tmp_path)

        insecure_issues = [i for i in issues if i.code == "INSECURE_URL_SCHEME"]
        assert len(insecure_issues) > 0
        assert insecure_issues[0].severity == "warning"

    def test_collect_issues_missing_path_slash(self, monkeypatch, tmp_path):
        """Test that missing leading slash in paths is detected."""
        monkeypatch.setenv("SONOTHEIA_DEEPFAKE_PATH", "v1/voice/deepfake")
        issues = collect_issues(tmp_path)

        path_issues = [i for i in issues if i.code == "MISSING_PATH_SLASH"]
        assert len(path_issues) > 0


class TestAPIConfig:
    """Tests for APIConfig dataclass."""

    def test_to_dict(self):
        """Test that APIConfig can be converted to dictionary."""
        config = APIConfig(
            api_key="test-key",
            api_url="https://api.example.com",
            deepfake_path="/v1/deepfake",
            mfa_path="/v1/mfa",
            sar_path="/v1/sar",
            timeout=30,
        )

        result = config.to_dict()
        assert isinstance(result, dict)
        assert result["api_url"] == "https://api.example.com"
        assert result["deepfake_path"] == "/v1/deepfake"
        # Note: api_key should NOT be in to_dict for security
        assert "api_key" not in result


class TestCheckFFmpegInstalled:
    """Tests for check_ffmpeg_installed function."""

    def test_check_ffmpeg_installed(self):
        """Test that ffmpeg check returns a tuple."""
        is_installed, message = check_ffmpeg_installed()
        assert isinstance(is_installed, bool)
        assert isinstance(message, str)
        assert len(message) > 0
