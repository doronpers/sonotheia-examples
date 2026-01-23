"""
Tests for constants module.

This module tests the shared constants used across the Sonotheia Python examples.
"""

from __future__ import annotations

from constants import ALLOWED_AUDIO_EXTENSIONS, AUDIO_MIME_TYPES, DEFAULT_AUDIO_MIME_TYPE


class TestAllowedAudioExtensions:
    """Tests for ALLOWED_AUDIO_EXTENSIONS constant."""

    def test_contains_expected_formats(self):
        """Test that all expected audio formats are included."""
        expected_formats = {".wav", ".opus", ".mp3", ".flac"}
        assert ALLOWED_AUDIO_EXTENSIONS == expected_formats

    def test_is_set_type(self):
        """Test that ALLOWED_AUDIO_EXTENSIONS is a set."""
        assert isinstance(ALLOWED_AUDIO_EXTENSIONS, set)

    def test_all_extensions_have_dot_prefix(self):
        """Test that all extensions start with a dot."""
        for ext in ALLOWED_AUDIO_EXTENSIONS:
            assert ext.startswith("."), f"Extension {ext} should start with '.'"

    def test_extensions_are_lowercase(self):
        """Test that all extensions are lowercase."""
        for ext in ALLOWED_AUDIO_EXTENSIONS:
            assert ext == ext.lower(), f"Extension {ext} should be lowercase"


class TestAudioMimeTypes:
    """Tests for AUDIO_MIME_TYPES constant."""

    def test_mapping_complete(self):
        """Test that MIME types are defined for all allowed extensions."""
        for ext in ALLOWED_AUDIO_EXTENSIONS:
            assert ext in AUDIO_MIME_TYPES, f"MIME type missing for {ext}"

    def test_mime_types_are_strings(self):
        """Test that all MIME types are strings."""
        for mime_type in AUDIO_MIME_TYPES.values():
            assert isinstance(mime_type, str)
            assert "/" in mime_type, "MIME types should contain '/' separator"

    def test_expected_mime_types(self):
        """Test that expected MIME types are correct."""
        assert AUDIO_MIME_TYPES[".wav"] == "audio/wav"
        assert AUDIO_MIME_TYPES[".opus"] == "audio/opus"
        assert AUDIO_MIME_TYPES[".mp3"] == "audio/mpeg"
        assert AUDIO_MIME_TYPES[".flac"] == "audio/flac"

    def test_is_dict_type(self):
        """Test that AUDIO_MIME_TYPES is a dictionary."""
        assert isinstance(AUDIO_MIME_TYPES, dict)


class TestDefaultAudioMimeType:
    """Tests for DEFAULT_AUDIO_MIME_TYPE constant."""

    def test_is_string(self):
        """Test that default MIME type is a string."""
        assert isinstance(DEFAULT_AUDIO_MIME_TYPE, str)

    def test_has_expected_value(self):
        """Test that default MIME type has expected value."""
        assert DEFAULT_AUDIO_MIME_TYPE == "application/octet-stream"

    def test_is_valid_mime_type_format(self):
        """Test that default MIME type follows MIME type format."""
        assert "/" in DEFAULT_AUDIO_MIME_TYPE


class TestConstantsImmutability:
    """Tests to ensure constants are not accidentally modified."""

    def test_allowed_extensions_immutable(self):
        """Test that ALLOWED_AUDIO_EXTENSIONS cannot be easily modified."""
        original = ALLOWED_AUDIO_EXTENSIONS.copy()
        # Attempting to modify should not affect the original
        # (This is a set, so we test that it's not accidentally reassigned)
        assert ALLOWED_AUDIO_EXTENSIONS == original

    def test_mime_types_immutable(self):
        """Test that AUDIO_MIME_TYPES cannot be easily modified."""
        original = AUDIO_MIME_TYPES.copy()
        # Attempting to modify should not affect the original
        assert AUDIO_MIME_TYPES == original


class TestConstantsModule:
    """Tests for constants module itself."""

    def test_module_imports_successfully(self):
        """Test that constants module can be imported."""
        import constants

        assert hasattr(constants, "ALLOWED_AUDIO_EXTENSIONS")
        assert hasattr(constants, "AUDIO_MIME_TYPES")
        assert hasattr(constants, "DEFAULT_AUDIO_MIME_TYPE")

    def test_constants_are_accessible(self):
        """Test that all constants are accessible after import."""
        from constants import ALLOWED_AUDIO_EXTENSIONS, AUDIO_MIME_TYPES, DEFAULT_AUDIO_MIME_TYPE

        assert ALLOWED_AUDIO_EXTENSIONS is not None
        assert AUDIO_MIME_TYPES is not None
        assert DEFAULT_AUDIO_MIME_TYPE is not None
