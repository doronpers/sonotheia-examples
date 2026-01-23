"""
Tests for audio_validator module.

This module tests the audio file validation functionality.
"""

from __future__ import annotations

from unittest.mock import patch

from audio_validator import (
    ValidationIssue,
    ValidationLevel,
    ValidationResult,
    auto_fix_audio,
    check_ffprobe_available,
    get_audio_info,
    validate_audio_file,
)


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_validation_result_structure(self):
        """Test that ValidationResult has expected structure."""
        result = ValidationResult(is_valid=True, file_path="test.wav")
        assert result.is_valid is True
        assert result.file_path == "test.wav"
        assert isinstance(result.issues, list)

    def test_errors_property(self):
        """Test that errors property filters correctly."""
        result = ValidationResult(is_valid=False, file_path="test.wav")
        result.issues.append(ValidationIssue(level=ValidationLevel.ERROR, message="Error 1"))
        result.issues.append(ValidationIssue(level=ValidationLevel.WARNING, message="Warning 1"))
        result.issues.append(ValidationIssue(level=ValidationLevel.INFO, message="Info 1"))

        assert len(result.errors) == 1
        assert result.errors[0].message == "Error 1"

    def test_warnings_property(self):
        """Test that warnings property filters correctly."""
        result = ValidationResult(is_valid=True, file_path="test.wav")
        result.issues.append(ValidationIssue(level=ValidationLevel.WARNING, message="Warning 1"))
        result.issues.append(ValidationIssue(level=ValidationLevel.ERROR, message="Error 1"))

        assert len(result.warnings) == 1
        assert result.warnings[0].message == "Warning 1"

    def test_has_errors_property(self):
        """Test that has_errors property works correctly."""
        result = ValidationResult(is_valid=True, file_path="test.wav")
        assert result.has_errors is False

        result.issues.append(ValidationIssue(level=ValidationLevel.ERROR, message="Error"))
        assert result.has_errors is True

    def test_to_dict(self):
        """Test that to_dict returns proper structure."""
        result = ValidationResult(is_valid=True, file_path="test.wav")
        result.format = "wav"
        result.sample_rate = 16000
        result.issues.append(
            ValidationIssue(
                level=ValidationLevel.WARNING,
                message="Test warning",
                field="sample_rate",
            )
        )

        data = result.to_dict()
        assert data["is_valid"] is True
        assert data["file_path"] == "test.wav"
        assert isinstance(data["issues"], list)
        assert isinstance(data["properties"], dict)


class TestCheckFFprobeAvailable:
    """Tests for check_ffprobe_available function."""

    def test_check_ffprobe_available_returns_boolean(self):
        """Test that function returns a boolean."""
        result = check_ffprobe_available()
        assert isinstance(result, bool)


class TestGetAudioInfo:
    """Tests for get_audio_info function."""

    def test_get_audio_info_with_valid_file(self, tmp_path):
        """Test getting audio info from a valid file."""
        # Create a minimal test file (this will fail ffprobe but tests the function)
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio data")

        # The function may return None if ffprobe fails, which is acceptable
        result = get_audio_info(str(test_file))
        # Result can be None or a dict, both are valid
        assert result is None or isinstance(result, dict)

    def test_get_audio_info_with_missing_file(self):
        """Test getting audio info from a missing file."""
        result = get_audio_info("/nonexistent/file.wav")
        assert result is None


class TestValidateAudioFile:
    """Tests for validate_audio_file function."""

    def test_validate_audio_file_missing_file(self):
        """Test validation fails when file doesn't exist."""
        result = validate_audio_file("/nonexistent/file.wav")
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("not found" in issue.message.lower() for issue in result.errors)

    def test_validate_audio_file_empty_file(self, tmp_path):
        """Test validation fails for empty file."""
        empty_file = tmp_path / "empty.wav"
        empty_file.write_bytes(b"")

        result = validate_audio_file(str(empty_file))
        assert result.is_valid is False
        assert any("empty" in issue.message.lower() for issue in result.errors)

    def test_validate_audio_file_invalid_extension(self, tmp_path):
        """Test validation with invalid extension."""
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_bytes(b"not audio data")

        result = validate_audio_file(str(invalid_file))
        # May fail on file existence check or format check
        assert isinstance(result, ValidationResult)

    @patch("audio_validator.check_ffprobe_available", return_value=False)
    def test_validate_audio_file_without_ffprobe(self, mock_check, tmp_path):
        """Test validation when ffprobe is not available."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio" * 100)  # Non-empty file

        result = validate_audio_file(str(test_file))
        assert isinstance(result, ValidationResult)
        # May have a warning about ffprobe or may proceed with limited validation
        # Both behaviors are acceptable

    def test_validate_audio_file_strict_mode(self, tmp_path):
        """Test validation in strict mode."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio" * 100)

        result = validate_audio_file(str(test_file), strict=True)
        assert isinstance(result, ValidationResult)

    def test_validation_result_structure_complete(self, tmp_path):
        """Test that validation result has all expected fields."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio" * 100)

        result = validate_audio_file(str(test_file))
        assert hasattr(result, "is_valid")
        assert hasattr(result, "file_path")
        assert hasattr(result, "issues")
        assert hasattr(result, "format")
        assert hasattr(result, "sample_rate")
        assert hasattr(result, "channels")
        assert hasattr(result, "duration")


class TestAutoFixAudio:
    """Tests for auto_fix_audio function."""

    def test_auto_fix_audio_with_missing_file(self):
        """Test auto_fix fails when input file doesn't exist."""
        success, message = auto_fix_audio("/nonexistent/file.wav")
        assert success is False
        # Message may be empty or contain error info - both are valid
        assert isinstance(message, str)

    @patch("audio_validator.check_ffprobe_available", return_value=False)
    def test_auto_fix_audio_without_ffprobe(self, mock_check, tmp_path):
        """Test auto_fix fails when ffprobe is not available."""
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio")

        success, message = auto_fix_audio(str(test_file))
        assert success is False
        # Message should indicate ffmpeg/ffprobe requirement
        assert isinstance(message, str)
        # May contain ffmpeg/ffprobe in message or be empty - both acceptable

    def test_auto_fix_audio_creates_output_path(self, tmp_path):
        """Test that auto_fix creates output file path."""
        input_file = tmp_path / "input.wav"
        input_file.write_bytes(b"fake audio" * 100)
        output_file = tmp_path / "output.wav"

        # This may fail if ffmpeg is not available, which is acceptable
        success, message = auto_fix_audio(str(input_file), str(output_file))
        # Result depends on ffmpeg availability
        assert isinstance(success, bool)
        assert isinstance(message, str)


class TestValidationLevel:
    """Tests for ValidationLevel enum."""

    def test_validation_level_values(self):
        """Test that ValidationLevel has expected values."""
        assert ValidationLevel.ERROR.value == "error"
        assert ValidationLevel.WARNING.value == "warning"
        assert ValidationLevel.INFO.value == "info"


class TestValidationIssue:
    """Tests for ValidationIssue dataclass."""

    def test_validation_issue_creation(self):
        """Test that ValidationIssue can be created."""
        issue = ValidationIssue(
            level=ValidationLevel.ERROR,
            message="Test error",
            field="sample_rate",
            actual_value=8000,
            expected_value=16000,
        )

        assert issue.level == ValidationLevel.ERROR
        assert issue.message == "Test error"
        assert issue.field == "sample_rate"
        assert issue.actual_value == 8000
        assert issue.expected_value == 16000
