"""Audio loading, slicing, and preprocessing."""

from enum import Enum
from pathlib import Path

import numpy as np
import soundfile as sf  # type: ignore
from scipy import signal  # type: ignore


class ResampleBackend(Enum):
    """Available resampling backends."""

    SCIPY = "scipy"
    LIBROSA = "librosa"


# Check if librosa is available
try:
    import librosa  # type: ignore

    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


class AudioSlice:
    """Represents a slice of audio data."""

    def __init__(
        self,
        data: np.ndarray,
        sample_rate: int,
        start_time: float,
        duration: float,
        slice_index: int,
    ):
        self.data = data
        self.sample_rate = sample_rate
        self.start_time = start_time
        self.duration = duration
        self.slice_index = slice_index

    @property
    def num_samples(self) -> int:
        return len(self.data)


def load_audio(
    file_path: Path,
    target_sr: int = 16000,
    resample_backend: ResampleBackend | str = ResampleBackend.SCIPY,
) -> tuple[np.ndarray, int]:
    """
    Load audio file and resample to target sample rate if needed.

    Args:
        file_path: Path to WAV file
        target_sr: Target sample rate in Hz (default: 16000)
        resample_backend: Backend to use for resampling (default: scipy)
            - "scipy": Uses scipy.signal.resample (adequate for stress testing)
            - "librosa": Uses librosa.resample (higher quality, requires librosa)

    Returns:
        Tuple of (audio_data, sample_rate)

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported, loading fails, or
                   librosa backend is requested but not available
    """
    # Normalize backend to enum
    if isinstance(resample_backend, str):
        try:
            resample_backend = ResampleBackend(resample_backend.lower())
        except ValueError:
            raise ValueError(
                f"Invalid resample backend: '{resample_backend}'. "
                f"Valid options: {', '.join(b.value for b in ResampleBackend)}"
            )

    # Check librosa availability
    if resample_backend == ResampleBackend.LIBROSA and not LIBROSA_AVAILABLE:
        raise ValueError(
            "Librosa backend requested but librosa is not installed. "
            "Install with: pip install librosa"
        )

    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    try:
        # Load audio with soundfile
        data, sr = sf.read(file_path, dtype="float32")

        # Convert stereo to mono if needed
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)

        # Resample if needed
        if sr != target_sr:
            if resample_backend == ResampleBackend.LIBROSA:
                # Use librosa for higher-quality resampling
                data = librosa.resample(data, orig_sr=sr, target_sr=target_sr)
            else:
                # Use scipy.signal.resample (default)
                num_samples = int(len(data) * target_sr / sr)
                if num_samples <= 0:
                    raise ValueError(
                        f"Invalid resampling: {sr} Hz to {target_sr} Hz "
                        f"would produce {num_samples} samples"
                    )
                data = signal.resample(data, num_samples)
            sr = target_sr

        return data, sr

    except ValueError:
        # Re-raise ValueError as-is (includes our custom message above)
        raise
    except (RuntimeError, OSError) as e:
        # Catch soundfile or scipy errors
        raise ValueError(f"Failed to load audio file {file_path}: {e}")


def slice_audio(
    audio_data: np.ndarray,
    sample_rate: int,
    slice_seconds: float = 10.0,
    hop_seconds: float = 10.0,
    max_slices: int | None = None,
) -> list[AudioSlice]:
    """
    Slice audio into fixed-duration segments.

    Args:
        audio_data: Audio samples
        sample_rate: Sample rate in Hz
        slice_seconds: Duration of each slice in seconds
        hop_seconds: Hop duration between slices in seconds
        max_slices: Maximum number of slices to create (None = all)

    Returns:
        List of AudioSlice objects
    """
    if slice_seconds <= 0:
        raise ValueError("slice_seconds must be positive.")
    if hop_seconds <= 0:
        raise ValueError("hop_seconds must be positive.")
    if max_slices is not None and max_slices <= 0:
        raise ValueError("max_slices must be positive.")

    slice_samples = int(slice_seconds * sample_rate)
    hop_samples = int(hop_seconds * sample_rate)

    slices = []
    slice_index = 0

    for start_sample in range(0, len(audio_data), hop_samples):
        # Stop if we've reached max_slices
        if max_slices is not None and slice_index >= max_slices:
            break

        end_sample = start_sample + slice_samples

        # Skip if slice would extend beyond audio
        if end_sample > len(audio_data):
            break

        slice_data = audio_data[start_sample:end_sample]
        start_time = start_sample / sample_rate
        duration = len(slice_data) / sample_rate

        slices.append(
            AudioSlice(
                data=slice_data,
                sample_rate=sample_rate,
                start_time=start_time,
                duration=duration,
                slice_index=slice_index,
            )
        )

        slice_index += 1

    return slices


def detect_clipping(audio_data: np.ndarray, threshold: float = 0.95) -> bool:
    """
    Detect if audio is clipped (samples near maximum amplitude).

    Args:
        audio_data: Audio samples
        threshold: Amplitude threshold (0-1) for clipping detection

    Returns:
        True if clipping detected
    """
    max_amp = np.max(np.abs(audio_data))
    return bool(max_amp >= threshold)
