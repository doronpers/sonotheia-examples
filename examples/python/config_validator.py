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

Auto-fix mode:
    from config_validator import validate_and_fix

    issues, fixes = validate_and_fix(auto_fix=True)
    for fix in fixes:
        print(fix)
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
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


@dataclass
class ConfigIssue:
    """Represents a detected configuration issue."""

    code: str  # Machine-readable code for the issue
    message: str  # Human-readable message
    severity: str  # 'error', 'warning', 'info'
    key: str | None = None  # Environment variable or file affected
    current_value: str | None = None  # Current value if applicable
    suggested_fix: str | None = None  # Suggested fix description
    auto_fixable: bool = False  # Whether this can be auto-fixed


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


def collect_issues(project_root: Path | None = None) -> list[ConfigIssue]:
    """
    Collect all configuration issues without raising exceptions.

    Args:
        project_root: Root directory of the project (defaults to current directory)

    Returns:
        List of ConfigIssue objects describing all detected issues
    """
    issues: list[ConfigIssue] = []
    root = project_root or Path.cwd()

    # Check for .env file
    env_file = root / ".env"
    env_example = root / ".env.example"

    if not env_file.exists():
        if env_example.exists():
            issues.append(
                ConfigIssue(
                    code="MISSING_ENV_FILE",
                    message=".env file not found",
                    severity="error",
                    key=".env",
                    suggested_fix="Copy .env.example to .env and fill in your API key",
                    auto_fixable=True,
                )
            )
        else:
            issues.append(
                ConfigIssue(
                    code="MISSING_ENV_FILE",
                    message=".env file not found (no .env.example available)",
                    severity="error",
                    key=".env",
                    suggested_fix="Create .env file with SONOTHEIA_API_KEY=your_key",
                    auto_fixable=False,
                )
            )

    # Check API key
    api_key = os.getenv("SONOTHEIA_API_KEY", "")
    if not api_key:
        issues.append(
            ConfigIssue(
                code="MISSING_API_KEY",
                message="SONOTHEIA_API_KEY environment variable not set",
                severity="error",
                key="SONOTHEIA_API_KEY",
                suggested_fix="Set SONOTHEIA_API_KEY in .env or environment",
                auto_fixable=False,
            )
        )
    elif api_key == "your_api_key_here" or api_key.startswith("YOUR_"):
        issues.append(
            ConfigIssue(
                code="PLACEHOLDER_API_KEY",
                message="SONOTHEIA_API_KEY contains a placeholder value",
                severity="error",
                key="SONOTHEIA_API_KEY",
                current_value=api_key[:10] + "...",
                suggested_fix="Replace placeholder with your actual API key",
                auto_fixable=False,
            )
        )

    # Check API URL scheme
    api_url = os.getenv("SONOTHEIA_API_URL", "")
    if api_url:
        if api_url.startswith("http://") and "localhost" not in api_url:
            issues.append(
                ConfigIssue(
                    code="INSECURE_URL_SCHEME",
                    message="SONOTHEIA_API_URL uses insecure http:// (should be https://)",
                    severity="warning",
                    key="SONOTHEIA_API_URL",
                    current_value=api_url,
                    suggested_fix="Change http:// to https://",
                    auto_fixable=True,
                )
            )

    # Check endpoint paths
    for var_name, default in [
        ("SONOTHEIA_DEEPFAKE_PATH", "/v1/voice/deepfake"),
        ("SONOTHEIA_MFA_PATH", "/v1/mfa/voice/verify"),
        ("SONOTHEIA_SAR_PATH", "/v1/reports/sar"),
    ]:
        path = os.getenv(var_name, "")
        if path and not path.startswith("/"):
            issues.append(
                ConfigIssue(
                    code="MISSING_PATH_SLASH",
                    message=f"{var_name} should start with /",
                    severity="warning",
                    key=var_name,
                    current_value=path,
                    suggested_fix=f"Add leading slash: /{path}",
                    auto_fixable=True,
                )
            )

    return issues


def validate_and_fix(
    project_root: Path | None = None,
    auto_fix: bool = False,
    confirm_fixes: bool = True,
) -> tuple[list[ConfigIssue], list[str]]:
    """
    Validate configuration and optionally auto-fix issues.

    Args:
        project_root: Root directory of the project (defaults to current directory)
        auto_fix: If True, attempt to auto-fix fixable issues
        confirm_fixes: If True, prompt user before applying each fix

    Returns:
        Tuple of (list of remaining issues, list of applied fix descriptions)
    """
    root = project_root or Path.cwd()
    issues = collect_issues(root)
    fixes_applied: list[str] = []

    if not auto_fix:
        return issues, fixes_applied

    remaining_issues: list[ConfigIssue] = []

    for issue in issues:
        if not issue.auto_fixable:
            remaining_issues.append(issue)
            continue

        # Prompt for confirmation if requested
        if confirm_fixes:
            print(f"\n⚠️  Issue: {issue.message}")
            print(f"   Suggested fix: {issue.suggested_fix}")
            response = input("   Apply fix? [y/N]: ").strip().lower()
            if response not in ("y", "yes"):
                remaining_issues.append(issue)
                continue

        # Apply fix based on issue code
        if issue.code == "MISSING_ENV_FILE":
            env_example = root / ".env.example"
            env_file = root / ".env"
            if env_example.exists():
                shutil.copy(env_example, env_file)
                fixes_applied.append("✅ Created .env from .env.example")

        elif issue.code == "INSECURE_URL_SCHEME":
            # Fix in .env file if it exists
            env_file = root / ".env"
            if env_file.exists() and issue.current_value:
                content = env_file.read_text()
                new_url = issue.current_value.replace("http://", "https://", 1)
                new_content = content.replace(issue.current_value, new_url)
                env_file.write_text(new_content)
                fixes_applied.append(f"✅ Fixed {issue.key} to use HTTPS")

        elif issue.code == "MISSING_PATH_SLASH":
            # Fix in .env file if it exists
            env_file = root / ".env"
            if env_file.exists() and issue.key and issue.current_value:
                content = env_file.read_text()
                new_value = f"/{issue.current_value}"
                old_line = f"{issue.key}={issue.current_value}"
                new_line = f"{issue.key}={new_value}"
                if old_line in content:
                    new_content = content.replace(old_line, new_line)
                    env_file.write_text(new_content)
                    fixes_applied.append(f"✅ Fixed {issue.key} path to include leading slash")

    return remaining_issues, fixes_applied


if __name__ == "__main__":
    """Example usage and self-test."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Sonotheia Configuration Validator")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix detected issues",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompts when fixing",
    )
    args = parser.parse_args()

    # Collect and display issues
    print("🔍 Checking Sonotheia configuration...\n")

    issues = collect_issues()

    if issues:
        print(f"Found {len(issues)} issue(s):\n")
        for i, issue in enumerate(issues, 1):
            icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(issue.severity, "•")
            print(f"  {i}. {icon} [{issue.code}] {issue.message}")
            if issue.suggested_fix:
                print(f"      Fix: {issue.suggested_fix}")
            if issue.current_value:
                print(f"      Current: {issue.current_value}")
        print()

        # Auto-fix if requested
        if args.fix:
            remaining, fixes = validate_and_fix(
                auto_fix=True,
                confirm_fixes=not args.no_confirm,
            )
            if fixes:
                print("\nFixes applied:")
                for fix in fixes:
                    print(f"  {fix}")
            if remaining:
                print(f"\n{len(remaining)} issue(s) still require manual attention")
                sys.exit(1)
            else:
                print("\n✅ All issues resolved!")
                sys.exit(0)
        else:
            print("Run with --fix to auto-fix issues")
            sys.exit(1)

    # If no issues, try full validation
    try:
        config = validate_api_config()
        print("✅ Configuration validation successful!")
        print(f"\nAPI URL: {config.api_url}")
        print(f"Timeout: {config.timeout}s")
        print("\nEndpoints:")
        print(f"  Deepfake: {config.api_url}{config.deepfake_path}")
        print(f"  MFA:      {config.api_url}{config.mfa_path}")
        print(f"  SAR:      {config.api_url}{config.sar_path}")

        # Check ffmpeg
        ffmpeg_ok, ffmpeg_msg = check_ffmpeg_installed()
        print(f"\nFFmpeg: {'✅ OK' if ffmpeg_ok else '⚠️ NOT FOUND'}")
        print(f"  {ffmpeg_msg}")

        sys.exit(0)

    except ConfigValidationError as exc:
        print(f"❌ Configuration validation failed: {exc}", file=sys.stderr)
        sys.exit(1)
