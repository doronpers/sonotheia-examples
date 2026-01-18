"""
Configuration constants for the audio trust harness.

Centralizes magic numbers, thresholds, and parameters used throughout
the detection pipeline to improve maintainability and configurability.

Configuration can be loaded from YAML files in the config/ directory.
If files are missing or parameters not specified, falls back to
hardcoded defaults.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class STFTConfig:
    """Configuration for Short-Time Fourier Transform (STFT) analysis.

    These parameters control spectral analysis across all spectral indicators.
    Frame size and overlap affect temporal and frequency resolution tradeoff.

    Attributes:
        nperseg: Number of samples per FFT segment (default: 2048)
                 At 16kHz, 2048 samples = 128ms window
        noverlap: Number of samples overlapping between segments (default: 1024)
                  50% overlap provides good time-frequency resolution balance
        window: Window function used for STFT (default: 'hann')
                Hann window reduces spectral leakage
    """

    nperseg: int = 2048
    noverlap: int = 1024
    window: str = "hann"


@dataclass(frozen=True)
class DeferralPolicyConfig:
    """Configuration for deferral policy decision making.

    Attributes:
        fragility_threshold: CV threshold for fragility detection (default: 0.3)
                           Higher values are more tolerant to variation
        clipping_threshold: Amplitude threshold for clipping detection (default: 0.95)
                          Signals exceeding this are considered clipped
        min_duration: Minimum slice duration in seconds (default: 0.5)
                     Shorter slices lack sufficient evidence for evaluation
        min_mean_threshold: Minimum absolute mean value for CV calculation (default: 1e-10)
                          Values below this are considered near-zero
    """

    fragility_threshold: float = 0.3
    clipping_threshold: float = 0.95
    min_duration: float = 0.5
    min_mean_threshold: float = 1e-10


@dataclass(frozen=True)
class ConsistencyConfig:
    """Configuration for cross-slice temporal consistency checking.

    Attributes:
        threshold: Threshold for temporal variation detection (default: 0.5)
                  Higher values are more tolerant to temporal changes
        min_value_threshold: Minimum absolute value for relative change calculation (default: 1e-10)
                           Values below this use robust change metric instead
    """

    threshold: float = 0.5
    min_value_threshold: float = 1e-10


@dataclass(frozen=True)
class PerturbationConfig:
    """Configuration for audio perturbations.

    Attributes:
        silent_audio_threshold: Power threshold to detect silent audio (default: 1e-10)
        silent_audio_reference_power: Reference power for silent audio (default: 1e-8)
                                     Reduced from 1e-6 to be more conservative
        epsilon: Small value to prevent numerical issues (default: 1e-10)
    """

    silent_audio_threshold: float = 1e-10
    silent_audio_reference_power: float = 1e-8
    epsilon: float = 1e-10


@dataclass(frozen=True)
class SpectralConfig:
    """Configuration for spectral indicators.

    Attributes:
        rolloff_percent: Percentage of energy for spectral rolloff (default: 0.85)
        min_power_threshold: Minimum power to include frequency bins (default: 1e-10)
                           Prevents log(0) and numerical issues
    """

    rolloff_percent: float = 0.85
    min_power_threshold: float = 1e-10


def _find_config_dir() -> Path | None:
    """
    Find the config directory by searching up from current file.

    Searches for:
    1. Directory specified in AUDIO_TRUST_CONFIG_DIR environment variable
    2. 'config' directory in parent directories (up to 3 levels)

    Returns:
        Path to config directory if found, None otherwise
    """
    # Check environment variable first
    env_config_dir = os.environ.get("AUDIO_TRUST_CONFIG_DIR")
    if env_config_dir:
        config_path = Path(env_config_dir)
        if config_path.is_dir():
            return config_path

    # Start from the package root (parent of parent of this file)
    current = Path(__file__).parent.parent.parent

    # Search up to 3 levels for config/ directory
    for _ in range(3):
        config_dir = current / "config"
        if config_dir.is_dir():
            return config_dir
        current = current.parent

    return None


def _load_yaml_config(filename: str) -> dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        filename: Name of YAML file in config/ directory

    Returns:
        Dictionary of configuration values, or empty dict if file not found
    """
    config_dir = _find_config_dir()

    if config_dir is None:
        return {}

    config_file = config_dir / filename

    if not config_file.exists():
        return {}

    try:
        with open(config_file, "r") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        # YAML parsing error - log warning and use defaults
        import warnings

        warnings.warn(f"Parse error {config_file}: {e}", UserWarning, stacklevel=2)
        return {}
    except OSError as e:
        # File permission or I/O error
        import warnings

        warnings.warn(f"Read error {config_file}: {e}", UserWarning, stacklevel=2)
        return {}


def _load_stft_config() -> STFTConfig:
    """Load STFT configuration from YAML or use defaults."""
    config = _load_yaml_config("indicators.yaml")
    stft_config = config.get("stft", {})

    return STFTConfig(
        nperseg=stft_config.get("nperseg", 2048),
        noverlap=stft_config.get("noverlap", 1024),
        window=stft_config.get("window", "hann"),
    )


def _load_deferral_policy_config() -> DeferralPolicyConfig:
    """Load deferral policy configuration from YAML or use defaults."""
    config = _load_yaml_config("thresholds.yaml")
    policy_config = config.get("deferral_policy", {})

    return DeferralPolicyConfig(
        fragility_threshold=policy_config.get("fragility_threshold", 0.3),
        clipping_threshold=policy_config.get("clipping_threshold", 0.95),
        min_duration=policy_config.get("min_duration", 0.5),
        min_mean_threshold=policy_config.get("min_mean_threshold", 1e-10),
    )


def _load_consistency_config() -> ConsistencyConfig:
    """Load consistency configuration from YAML or use defaults."""
    config = _load_yaml_config("thresholds.yaml")
    consistency_config = config.get("consistency", {})

    return ConsistencyConfig(
        threshold=consistency_config.get("threshold", 0.5),
        min_value_threshold=consistency_config.get("min_value_threshold", 1e-10),
    )


def _load_perturbation_config() -> PerturbationConfig:
    """Load perturbation configuration from YAML or use defaults."""
    config = _load_yaml_config("indicators.yaml")
    perturb_config = config.get("perturbation", {})

    return PerturbationConfig(
        silent_audio_threshold=perturb_config.get("silent_audio_threshold", 1e-10),
        silent_audio_reference_power=perturb_config.get("silent_audio_reference_power", 1e-8),
        epsilon=perturb_config.get("epsilon", 1e-10),
    )


def _load_spectral_config() -> SpectralConfig:
    """Load spectral configuration from YAML or use defaults."""
    config = _load_yaml_config("indicators.yaml")
    spectral_config = config.get("spectral", {})

    return SpectralConfig(
        rolloff_percent=spectral_config.get("rolloff_percent", 0.85),
        min_power_threshold=spectral_config.get("min_power_threshold", 1e-10),
    )


def get_perturbation_defaults(perturbation_name: str) -> dict[str, Any]:
    """
    Get default parameters for a perturbation from YAML config.

    Args:
        perturbation_name: Name of perturbation (e.g., 'noise', 'codec_stub')

    Returns:
        Dictionary of default parameters
    """
    config = _load_yaml_config("perturbations.yaml")
    return config.get(perturbation_name, {})


# Global configuration instances
# These can be imported and used throughout the codebase
STFT_CONFIG = STFTConfig()
DEFERRAL_POLICY_CONFIG = DeferralPolicyConfig()
CONSISTENCY_CONFIG = ConsistencyConfig()
PERTURBATION_CONFIG = PerturbationConfig()
SPECTRAL_CONFIG = SpectralConfig()


# Valid FFT window types supported by scipy.signal.stft
VALID_FFT_WINDOWS = [
    "hann",
    "hamming",
    "blackman",
    "bartlett",
    "boxcar",
    "triang",
    "flattop",
    "parzen",
    "bohman",
    "blackmanharris",
    "nuttall",
    "barthann",
]


def configure_stft(
    nperseg: int | None = None,
    noverlap: int | None = None,
    window: str | None = None,
) -> None:
    """Configure STFT parameters at runtime.

    This function updates the global STFT_CONFIG used by all spectral indicators.
    Call this before processing to customize FFT parameters.

    Args:
        nperseg: Number of samples per FFT segment (default: keep current)
        noverlap: Number of samples overlapping between segments (default: keep current)
        window: Window function name (default: keep current)
                Valid options: hann, hamming, blackman, bartlett, boxcar, etc.

    Raises:
        ValueError: If window type is not valid
    """
    global STFT_CONFIG

    if window is not None and window not in VALID_FFT_WINDOWS:
        raise ValueError(
            f"Invalid FFT window type: '{window}'. "
            f"Valid options: {', '.join(VALID_FFT_WINDOWS)}"
        )

    STFT_CONFIG = STFTConfig(
        nperseg=nperseg if nperseg is not None else STFT_CONFIG.nperseg,
        noverlap=noverlap if noverlap is not None else STFT_CONFIG.noverlap,
        window=window if window is not None else STFT_CONFIG.window,
    )


def get_stft_config() -> STFTConfig:
    """Get the current STFT configuration.

    Returns:
        Current STFTConfig instance
    """
    return STFT_CONFIG


def reset_config() -> None:
    """Reset all configuration to defaults.

    Useful for testing or resetting state between runs.
    """
    global STFT_CONFIG, DEFERRAL_POLICY_CONFIG, CONSISTENCY_CONFIG
    global PERTURBATION_CONFIG, SPECTRAL_CONFIG

    STFT_CONFIG = STFTConfig()
    DEFERRAL_POLICY_CONFIG = DeferralPolicyConfig()
    CONSISTENCY_CONFIG = ConsistencyConfig()
    PERTURBATION_CONFIG = PerturbationConfig()
    SPECTRAL_CONFIG = SpectralConfig()


# Values are loaded from YAML files with fallback to hardcoded defaults
STFT_CONFIG = _load_stft_config()
DEFERRAL_POLICY_CONFIG = _load_deferral_policy_config()
CONSISTENCY_CONFIG = _load_consistency_config()
PERTURBATION_CONFIG = _load_perturbation_config()
SPECTRAL_CONFIG = _load_spectral_config()
