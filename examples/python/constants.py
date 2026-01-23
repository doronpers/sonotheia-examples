"""
Shared constants for Sonotheia Python examples.

This module provides centralized constants to avoid duplication across files.
"""

from __future__ import annotations

# Supported audio file extensions
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".opus", ".mp3", ".flac"}

# MIME type mappings for audio formats
AUDIO_MIME_TYPES = {
    ".wav": "audio/wav",
    ".opus": "audio/opus",
    ".mp3": "audio/mpeg",
    ".flac": "audio/flac",
}

# Default MIME type for unknown audio formats
DEFAULT_AUDIO_MIME_TYPE = "application/octet-stream"
