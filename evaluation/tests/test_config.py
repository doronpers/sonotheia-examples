"""
Tests for configuration module.
"""

import pytest

from audio_trust_harness.config import (
    VALID_FFT_WINDOWS,
    STFTConfig,
    configure_stft,
    get_stft_config,
    reset_config,
)


class TestSTFTConfig:
    """Tests for STFTConfig dataclass."""

    def test_stft_config_defaults(self):
        """Test STFTConfig default values."""
        config = STFTConfig()

        assert config.nperseg == 2048
        assert config.noverlap == 1024
        assert config.window == "hann"

    def test_stft_config_custom_values(self):
        """Test STFTConfig with custom values."""
        config = STFTConfig(nperseg=4096, noverlap=2048, window="hamming")

        assert config.nperseg == 4096
        assert config.noverlap == 2048
        assert config.window == "hamming"

    def test_stft_config_is_frozen(self):
        """Test that STFTConfig is immutable."""
        config = STFTConfig()

        with pytest.raises(AttributeError):
            config.window = "blackman"


class TestConfigureSTFT:
    """Tests for configure_stft function."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    def teardown_method(self):
        """Reset config after each test."""
        reset_config()

    def test_configure_stft_window(self):
        """Test configuring just the window type."""
        configure_stft(window="hamming")
        config = get_stft_config()

        assert config.window == "hamming"
        # Other values should remain default
        assert config.nperseg == 2048
        assert config.noverlap == 1024

    def test_configure_stft_all_params(self):
        """Test configuring all STFT parameters."""
        configure_stft(nperseg=4096, noverlap=2048, window="blackman")
        config = get_stft_config()

        assert config.nperseg == 4096
        assert config.noverlap == 2048
        assert config.window == "blackman"

    def test_configure_stft_invalid_window(self):
        """Test that invalid window type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            configure_stft(window="invalid_window")

        assert "Invalid FFT window type" in str(exc_info.value)
        assert "invalid_window" in str(exc_info.value)

    def test_configure_stft_preserves_unchanged(self):
        """Test that unchanged parameters are preserved."""
        # First configure with custom values
        configure_stft(nperseg=4096, noverlap=2048, window="blackman")

        # Then only change window
        configure_stft(window="hamming")
        config = get_stft_config()

        # nperseg and noverlap should be preserved
        assert config.nperseg == 4096
        assert config.noverlap == 2048
        assert config.window == "hamming"


class TestValidFFTWindows:
    """Tests for VALID_FFT_WINDOWS list."""

    def test_valid_windows_contains_common_types(self):
        """Test that common window types are included."""
        common_windows = ["hann", "hamming", "blackman", "bartlett", "boxcar"]
        for window in common_windows:
            assert window in VALID_FFT_WINDOWS

    def test_all_valid_windows_can_be_configured(self):
        """Test that all valid window types can be configured."""
        for window in VALID_FFT_WINDOWS:
            reset_config()
            configure_stft(window=window)
            config = get_stft_config()
            assert config.window == window


class TestResetConfig:
    """Tests for reset_config function."""

    def test_reset_config_restores_defaults(self):
        """Test that reset_config restores all defaults."""
        # Configure with custom values
        configure_stft(nperseg=4096, noverlap=2048, window="blackman")

        # Verify custom values are set
        config = get_stft_config()
        assert config.window == "blackman"

        # Reset
        reset_config()

        # Verify defaults are restored
        config = get_stft_config()
        assert config.nperseg == 2048
        assert config.noverlap == 1024
        assert config.window == "hann"
