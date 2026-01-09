"""
Audio validation utility for Sonotheia API.

This module provides functions to validate audio files before submission to the API,
helping to catch issues early and reduce failed API calls.

Features:
- Format validation (WAV, MP3, Opus, FLAC)
- Sample rate checking (recommends 16 kHz)
- Channel count validation (recommends mono)
- Duration validation (3-10 seconds optimal)
- File size checking (< 10 MB)
- Audio quality assessment
- Corruption detection

Usage:
    python audio_validator.py audio.wav

    # Or as a library
    from audio_validator import validate_audio_file, ValidationResult

    result = validate_audio_file("audio.wav")
    if result.is_valid:
        # Submit to API
        client.detect_deepfake("audio.wav")
    else:
        # Handle validation errors
        for error in result.errors:
            print(f"Error: {error}")
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels."""

    ERROR = "error"  # Will likely cause API error
    WARNING = "warning"  # May cause poor results
    INFO = "info"  # Informational, optimal would be different


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""

    level: ValidationLevel
    message: str
    field: str | None = None
    actual_value: Any = None
    expected_value: Any = None


@dataclass
class ValidationResult:
    """Result of audio file validation."""

    is_valid: bool
    file_path: str
    issues: list[ValidationIssue] = field(default_factory=list)

    # Audio properties
    format: str | None = None
    codec: str | None = None
    sample_rate: int | None = None
    channels: int | None = None
    duration: float | None = None
    bit_rate: int | None = None
    file_size: int | None = None

    @property
    def errors(self) -> list[ValidationIssue]:
        """Get only error-level issues."""
        return [i for i in self.issues if i.level == ValidationLevel.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Get only warning-level issues."""
        return [i for i in self.issues if i.level == ValidationLevel.WARNING]

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_valid": self.is_valid,
            "file_path": self.file_path,
            "issues": [
                {
                    "level": i.level.value,
                    "message": i.message,
                    "field": i.field,
                    "actual_value": i.actual_value,
                    "expected_value": i.expected_value,
                }
                for i in self.issues
            ],
            "properties": {
                "format": self.format,
                "codec": self.codec,
                "sample_rate": self.sample_rate,
                "channels": self.channels,
                "duration": self.duration,
                "bit_rate": self.bit_rate,
                "file_size": self.file_size,
            },
        }


@lru_cache(maxsize=1)
def check_ffprobe_available() -> bool:
    """
    Check if ffprobe is available on the system.

    Cached to avoid repeated subprocess calls.

    Returns:
        True if ffprobe is available, False otherwise
    """
    try:
        subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            check=True,
            timeout=5,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_audio_info(file_path: str) -> dict[str, Any] | None:
    """
    Extract audio file information using ffprobe.

    Args:
        file_path: Path to audio file

    Returns:
        Dictionary with audio properties or None if extraction fails
    """
    try:
        command = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name,sample_rate,channels,bit_rate,duration:format=format_name,duration,size",
            "-of",
            "json",
            file_path,
        ]

        result = subprocess.run(command, capture_output=True, text=True, check=True)

        data = json.loads(result.stdout)

        # Extract stream and format info
        stream = data.get("streams", [{}])[0]
        format_info = data.get("format", {})

        return {
            "codec": stream.get("codec_name"),
            "sample_rate": int(stream.get("sample_rate", 0)),
            "channels": int(stream.get("channels", 0)),
            "bit_rate": int(stream.get("bit_rate", 0)),
            "stream_duration": float(stream.get("duration", 0)),
            "format": format_info.get("format_name"),
            "duration": float(format_info.get("duration", 0)),
            "size": int(format_info.get("size", 0)),
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"ffprobe failed: {e.stderr}")
        return None
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Failed to parse ffprobe output: {e}")
        return None


def validate_audio_file(file_path: str, strict: bool = False) -> ValidationResult:
    """
    Validate audio file for Sonotheia API submission.

    Args:
        file_path: Path to audio file
        strict: If True, warnings are treated as errors

    Returns:
        ValidationResult with validation details
    """
    result = ValidationResult(is_valid=True, file_path=file_path)

    # Check if file exists
    if not os.path.exists(file_path):
        result.is_valid = False
        result.issues.append(
            ValidationIssue(
                level=ValidationLevel.ERROR,
                message=f"File not found: {file_path}",
                field="file_path",
            )
        )
        return result

    # Check file size
    file_size = os.path.getsize(file_path)
    result.file_size = file_size

    max_size = 10 * 1024 * 1024  # 10 MB
    if file_size > max_size:
        result.is_valid = False
        result.issues.append(
            ValidationIssue(
                level=ValidationLevel.ERROR,
                message=f"File size {file_size / 1024 / 1024:.2f} MB exceeds maximum of 10 MB",
                field="file_size",
                actual_value=file_size,
                expected_value=max_size,
            )
        )

    if file_size == 0:
        result.is_valid = False
        result.issues.append(
            ValidationIssue(
                level=ValidationLevel.ERROR, message="File is empty (0 bytes)", field="file_size"
            )
        )
        return result

    # Check if ffprobe is available
    if not check_ffprobe_available():
        result.issues.append(
            ValidationIssue(
                level=ValidationLevel.WARNING,
                message="ffprobe not available - cannot perform detailed validation. Install with: apt-get install ffmpeg",
            )
        )
        return result

    # Get audio information
    audio_info = get_audio_info(file_path)

    if not audio_info:
        result.is_valid = False
        result.issues.append(
            ValidationIssue(
                level=ValidationLevel.ERROR,
                message="Failed to extract audio information - file may be corrupted",
                field="file",
            )
        )
        return result

    # Populate result properties
    result.format = audio_info.get("format")
    result.codec = audio_info.get("codec")
    result.sample_rate = audio_info.get("sample_rate")
    result.channels = audio_info.get("channels")
    result.duration = audio_info.get("duration", audio_info.get("stream_duration", 0))
    result.bit_rate = audio_info.get("bit_rate")

    # Validate format
    supported_formats = ["wav", "mp3", "opus", "ogg", "flac"]
    if result.format and not any(fmt in result.format.lower() for fmt in supported_formats):
        result.issues.append(
            ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"Format '{result.format}' may not be supported. Recommended: WAV, MP3, Opus, FLAC",
                field="format",
                actual_value=result.format,
                expected_value=supported_formats,
            )
        )

    # Validate codec
    recommended_codecs = ["pcm_s16le", "mp3", "opus", "flac"]
    if result.codec and result.codec not in recommended_codecs:
        result.issues.append(
            ValidationIssue(
                level=ValidationLevel.INFO,
                message=f"Codec '{result.codec}' is non-standard. Recommended: {', '.join(recommended_codecs)}",
                field="codec",
                actual_value=result.codec,
            )
        )

    # Validate sample rate
    optimal_sample_rate = 16000
    if result.sample_rate:
        if result.sample_rate < 8000:
            level = ValidationLevel.ERROR if strict else ValidationLevel.WARNING
            result.issues.append(
                ValidationIssue(
                    level=level,
                    message=f"Sample rate {result.sample_rate} Hz is very low. Minimum recommended: 8000 Hz",
                    field="sample_rate",
                    actual_value=result.sample_rate,
                    expected_value=8000,
                )
            )
            if level == ValidationLevel.ERROR:
                result.is_valid = False

        elif result.sample_rate != optimal_sample_rate:
            result.issues.append(
                ValidationIssue(
                    level=ValidationLevel.INFO,
                    message=f"Sample rate is {result.sample_rate} Hz. Optimal: {optimal_sample_rate} Hz",
                    field="sample_rate",
                    actual_value=result.sample_rate,
                    expected_value=optimal_sample_rate,
                )
            )

    # Validate channels
    if result.channels:
        if result.channels > 2:
            level = ValidationLevel.ERROR if strict else ValidationLevel.WARNING
            result.issues.append(
                ValidationIssue(
                    level=level,
                    message=f"Audio has {result.channels} channels. Recommended: 1 (mono)",
                    field="channels",
                    actual_value=result.channels,
                    expected_value=1,
                )
            )
            if level == ValidationLevel.ERROR:
                result.is_valid = False

        elif result.channels == 2:
            result.issues.append(
                ValidationIssue(
                    level=ValidationLevel.INFO,
                    message="Audio is stereo (2 channels). Optimal: mono (1 channel)",
                    field="channels",
                    actual_value=2,
                    expected_value=1,
                )
            )

    # Validate duration
    if result.duration:
        min_duration = 3.0
        max_optimal_duration = 10.0

        if result.duration < min_duration:
            result.is_valid = False
            result.issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Duration {result.duration:.2f}s is too short. Minimum: {min_duration}s",
                    field="duration",
                    actual_value=result.duration,
                    expected_value=min_duration,
                )
            )
        elif result.duration > max_optimal_duration:
            result.issues.append(
                ValidationIssue(
                    level=ValidationLevel.INFO,
                    message=f"Duration {result.duration:.2f}s exceeds optimal range. Optimal: 3-10s. Consider using streaming for long files.",
                    field="duration",
                    actual_value=result.duration,
                    expected_value=max_optimal_duration,
                )
            )

    return result


def auto_fix_audio(input_path: str, output_path: str | None = None) -> tuple[bool, str]:
    """
    Automatically fix common audio issues.

    Args:
        input_path: Path to input audio file
        output_path: Path for output file (defaults to input_fixed.wav)

    Returns:
        Tuple of (success, output_path)
    """
    if not check_ffprobe_available():
        logger.error("ffmpeg is required for auto-fix. Install with: apt-get install ffmpeg")
        return False, ""

    if output_path is None:
        stem = Path(input_path).stem
        output_path = f"{stem}_fixed.wav"

    logger.info(f"Auto-fixing audio: {input_path} -> {output_path}")

    try:
        command = [
            "ffmpeg",
            "-i",
            input_path,
            "-ar",
            "16000",  # Set sample rate to 16 kHz
            "-ac",
            "1",  # Convert to mono
            "-sample_fmt",
            "s16",  # 16-bit PCM
            "-y",  # Overwrite output
            output_path,
        ]

        subprocess.run(command, capture_output=True, text=True, check=True)

        logger.info(f"Audio fixed successfully: {output_path}")
        return True, output_path

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to fix audio: {e.stderr}")
        return False, ""


def print_validation_result(result: ValidationResult):
    """Pretty-print validation results."""

    print(f"\n{'=' * 60}")
    print(f"Validation Results: {result.file_path}")
    print(f"{'=' * 60}\n")

    # Overall status
    status_icon = "✅" if result.is_valid else "❌"
    print(f"Status: {status_icon} {'VALID' if result.is_valid else 'INVALID'}\n")

    # Audio properties
    if result.format or result.sample_rate or result.channels or result.duration:
        print("Audio Properties:")
        if result.format:
            print(f"  Format:      {result.format}")
        if result.codec:
            print(f"  Codec:       {result.codec}")
        if result.sample_rate:
            print(f"  Sample Rate: {result.sample_rate} Hz")
        if result.channels:
            print(f"  Channels:    {result.channels}")
        if result.duration:
            print(f"  Duration:    {result.duration:.2f}s")
        if result.file_size:
            print(f"  File Size:   {result.file_size / 1024:.2f} KB")
        print()

    # Issues
    if result.issues:
        # Errors
        if result.errors:
            print("❌ Errors:")
            for issue in result.errors:
                print(f"  - {issue.message}")
            print()

        # Warnings
        if result.warnings:
            print("⚠️  Warnings:")
            for issue in result.warnings:
                print(f"  - {issue.message}")
            print()

        # Info
        info_issues = [i for i in result.issues if i.level == ValidationLevel.INFO]
        if info_issues:
            print("ℹ️  Recommendations:")
            for issue in info_issues:
                print(f"  - {issue.message}")
            print()
    else:
        print("✨ No issues found - audio is optimal!\n")

    print(f"{'=' * 60}\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate audio files for Sonotheia API submission"
    )
    parser.add_argument("audio_file", help="Path to audio file to validate")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument(
        "--auto-fix", action="store_true", help="Automatically fix issues and create corrected file"
    )
    parser.add_argument("--output", help="Output path for auto-fixed file")

    args = parser.parse_args()

    # Validate the audio file
    result = validate_audio_file(args.audio_file, strict=args.strict)

    if args.json:
        # Output as JSON
        print(json.dumps(result.to_dict(), indent=2))
    else:
        # Pretty print
        print_validation_result(result)

    # Auto-fix if requested
    if args.auto_fix and not result.is_valid:
        print("Attempting to auto-fix issues...")
        success, output_path = auto_fix_audio(args.audio_file, args.output)

        if success:
            print(f"\n✅ Fixed file created: {output_path}")
            print("Validating fixed file...\n")

            fixed_result = validate_audio_file(output_path, strict=args.strict)
            print_validation_result(fixed_result)

            return 0 if fixed_result.is_valid else 1
        else:
            print("\n❌ Auto-fix failed. Please fix issues manually.")
            return 1

    # Exit with appropriate code
    return 0 if result.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
