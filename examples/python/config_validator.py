"""
Configuration validation utilities for Sonotheia API clients.

This module provides utilities to validate environment variables and configuration
settings before attempting API calls, helping catch configuration errors early.

Usage:
    from config_validator import validate_api_config, ConfigValidationError

    try:
        config = validate_api_config()
        # Use validated config
    except ConfigValidationError as e:
        print(f"Configuration error: {e}")
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


@dataclass
class APIConfig:
    """Validated API configuration."""

    api_key: str
    api_url: str
    deepfake_path: str
    mfa_path: str
    sar_path: str
    timeout: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "api_url": self.api_url,
            "deepfake_path": self.deepfake_path,
            "mfa_path": self.mfa_path,
            "sar_path": self.sar_path,
            "timeout": self.timeout,
        }


def validate_required_env(var_name: str, default: str | None = None) -> str:
    """
    Validate that a required environment variable is set.

    Args:
        var_name: Name of the environment variable
        default: Optional default value if not set

    Returns:
        Value of the environment variable

    Raises:
        ConfigValidationError: If the variable is not set and no default provided
    """
    value = os.getenv(var_name, default)
    if not value:
        raise ConfigValidationError(
            f"Required environment variable {var_name} is not set. "
            f"Please set it or provide it as a parameter."
        )
    return value


def validate_url(url: str, name: str = "URL") -> str:
    """
    Validate that a URL is properly formatted.

    Args:
        url: URL to validate
        name: Name of the URL for error messages

    Returns:
        Validated URL (with trailing slash removed)

    Raises:
        ConfigValidationError: If URL is invalid
    """
    if not url:
        raise ConfigValidationError(f"{name} cannot be empty")

    if not url.startswith(("http://", "https://")):
        raise ConfigValidationError(f"{name} must start with http:// or https://")

    return url.rstrip("/")


def validate_path(path: str, name: str = "Path") -> str:
    """
    Validate that an API path is properly formatted.

    Args:
        path: Path to validate
        name: Name of the path for error messages

    Returns:
        Validated path (with leading slash ensured)

    Raises:
        ConfigValidationError: If path is invalid
    """
    if not path:
        raise ConfigValidationError(f"{name} cannot be empty")

    if not path.startswith("/"):
        path = f"/{path}"

    return path


def validate_timeout(timeout: int | str, name: str = "Timeout") -> int:
    """
    Validate timeout value.

    Args:
        timeout: Timeout value in seconds
        name: Name of the timeout for error messages

    Returns:
        Validated timeout as integer

    Raises:
        ConfigValidationError: If timeout is invalid
    """
    try:
        timeout_int = int(timeout)
    except (ValueError, TypeError):
        raise ConfigValidationError(f"{name} must be a valid integer") from None

    if timeout_int <= 0:
        raise ConfigValidationError(f"{name} must be greater than 0")

    if timeout_int > 300:  # 5 minutes max
        raise ConfigValidationError(f"{name} should not exceed 300 seconds")

    return timeout_int


def validate_api_config(
    api_key: str | None = None,
    api_url: str | None = None,
    deepfake_path: str | None = None,
    mfa_path: str | None = None,
    sar_path: str | None = None,
    timeout: int | str | None = None,
) -> APIConfig:
    """
    Validate API configuration from parameters or environment variables.

    Args:
        api_key: API key (or None to read from SONOTHEIA_API_KEY)
        api_url: API URL (or None to read from SONOTHEIA_API_URL)
        deepfake_path: Deepfake endpoint path (or None to use default)
        mfa_path: MFA endpoint path (or None to use default)
        sar_path: SAR endpoint path (or None to use default)
        timeout: Request timeout in seconds (or None to use default)

    Returns:
        Validated APIConfig object

    Raises:
        ConfigValidationError: If any configuration is invalid
    """
    # Validate API key
    validated_api_key = validate_required_env(
        "SONOTHEIA_API_KEY", api_key if api_key else None
    )

    # Validate API URL
    raw_api_url = api_url or os.getenv("SONOTHEIA_API_URL", "https://api.sonotheia.com")
    validated_api_url = validate_url(raw_api_url, "API URL")

    # Validate paths
    validated_deepfake_path = validate_path(
        deepfake_path or os.getenv("SONOTHEIA_DEEPFAKE_PATH", "/v1/voice/deepfake"),
        "Deepfake endpoint path",
    )

    validated_mfa_path = validate_path(
        mfa_path or os.getenv("SONOTHEIA_MFA_PATH", "/v1/mfa/voice/verify"),
        "MFA endpoint path",
    )

    validated_sar_path = validate_path(
        sar_path or os.getenv("SONOTHEIA_SAR_PATH", "/v1/reports/sar"),
        "SAR endpoint path",
    )

    # Validate timeout
    raw_timeout = (
        timeout if timeout is not None else os.getenv("SONOTHEIA_TIMEOUT", "30")
    )
    validated_timeout = validate_timeout(raw_timeout)

    return APIConfig(
        api_key=validated_api_key,
        api_url=validated_api_url,
        deepfake_path=validated_deepfake_path,
        mfa_path=validated_mfa_path,
        sar_path=validated_sar_path,
        timeout=validated_timeout,
    )


def check_ffmpeg_installed() -> tuple[bool, str]:
    """
    Check if ffmpeg/ffprobe is installed and available.

    Returns:
        Tuple of (is_installed, message)
    """
    import subprocess

    try:
        subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            check=True,
            timeout=5,
        )
        return True, "ffmpeg is installed and available"
    except subprocess.TimeoutExpired:
        return False, "ffprobe check timed out"
    except subprocess.CalledProcessError:
        return False, "ffprobe is installed but returned an error"
    except FileNotFoundError:
        return False, "ffmpeg is not installed. Install with: apt-get install ffmpeg"


if __name__ == "__main__":
    """Example usage and self-test."""
    import sys

    try:
        config = validate_api_config()
        print("Configuration validation successful!")
        print(f"API URL: {config.api_url}")
        print(f"Timeout: {config.timeout}s")
        print("\nEndpoints:")
        print(f"  Deepfake: {config.api_url}{config.deepfake_path}")
        print(f"  MFA:      {config.api_url}{config.mfa_path}")
        print(f"  SAR:      {config.api_url}{config.sar_path}")

        # Check ffmpeg
        ffmpeg_ok, ffmpeg_msg = check_ffmpeg_installed()
        print(f"\nFFmpeg: {'OK' if ffmpeg_ok else 'NOT FOUND'}")
        print(f"  {ffmpeg_msg}")

        sys.exit(0)

    except ConfigValidationError as exc:
        print(f"Configuration validation failed: {exc}", file=sys.stderr)
        sys.exit(1)
