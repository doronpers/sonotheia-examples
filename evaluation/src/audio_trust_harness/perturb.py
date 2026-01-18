"""
Audio perturbations for stress testing.

All perturbations are deterministic when given a seed.
"""

import os
import tempfile
from typing import Any, cast

import librosa
import numpy as np
from pydub import AudioSegment
from scipy import signal

from audio_trust_harness.config import PERTURBATION_CONFIG, get_perturbation_defaults


class Perturbation:
    """Base class for audio perturbations."""

    def __init__(self, name: str, seed: int = 1337):
        self.name = name
        self.seed = seed
        self.rng = np.random.RandomState(seed)

    def apply(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply perturbation to audio data."""
        raise NotImplementedError

    def get_params(self) -> dict[str, Any]:
        """Get perturbation parameters for logging."""
        return {"seed": self.seed}


class NonePerturbation(Perturbation):
    """Identity perturbation (no change)."""

    def __init__(self, seed: int = 1337):
        super().__init__("none", seed)

    def apply(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Return audio unchanged."""
        return audio.copy()


class NoisePerturbation(Perturbation):
    """Additive Gaussian noise perturbation."""

    def __init__(self, snr_db: float | None = None, seed: int = 1337):
        super().__init__("noise", seed)
        # Load from config if not provided
        if snr_db is None:
            defaults = get_perturbation_defaults("noise")
            snr_db = defaults.get("snr_db", 20.0)
        self.snr_db = snr_db

    def apply(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Add white Gaussian noise at specified SNR.

        For silent or near-silent audio, uses a reference power to ensure
        consistent SNR behavior. The reference power is chosen conservatively
        to avoid overwhelming quiet audio with noise.
        """
        # Calculate signal power
        signal_power = np.mean(audio**2)

        # Handle silent audio case using config threshold
        if signal_power < PERTURBATION_CONFIG.silent_audio_threshold:
            # For silent audio, use a reference power
            # This is more conservative than before (1e-8 vs 1e-6)
            signal_power = PERTURBATION_CONFIG.silent_audio_reference_power

        # Calculate noise power from SNR
        snr_linear = 10 ** (self.snr_db / 10.0)
        noise_power = signal_power / snr_linear

        # Generate noise with correct power
        noise = self.rng.randn(len(audio))
        noise = noise * np.sqrt(noise_power)

        # Add noise to signal
        noisy_audio = audio + noise

        # Clip to valid range [-1, 1]
        noisy_audio = np.clip(noisy_audio, -1.0, 1.0)

        return cast(np.ndarray, noisy_audio.astype(np.float32))

    def get_params(self) -> dict[str, Any]:
        return {"snr_db": self.snr_db, "seed": self.seed}


class CodecStubPerturbation(Perturbation):
    """
    Codec approximation using lowpass filter + quantization.

    NOTE: This is NOT a real codec. It's a simple approximation for testing
    indicator robustness to spectral changes and quantization.
    """

    def __init__(self, cutoff_hz: float | None = None, bits: int | None = None, seed: int = 1337):
        super().__init__("codec_stub", seed)
        # Load from config if not provided
        defaults = get_perturbation_defaults("codec_stub")
        self.cutoff_hz = cutoff_hz if cutoff_hz is not None else defaults.get("cutoff_hz", 3400.0)
        self.bits = bits if bits is not None else defaults.get("bits", 8)

    def apply(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply lowpass filter and bit-depth quantization."""
        # Lowpass filter (approximates bandwidth limitation)
        nyquist = sample_rate / 2.0
        normalized_cutoff = self.cutoff_hz / nyquist

        # Only apply filter if cutoff is below Nyquist
        if normalized_cutoff < 1.0:
            sos = signal.butter(4, normalized_cutoff, btype="low", output="sos")
            filtered = signal.sosfilt(sos, audio)
        else:
            filtered = audio.copy()

        # Quantization (approximates lossy compression)
        levels = 2**self.bits
        quantized = np.round(filtered * (levels / 2)) / (levels / 2)

        # Clip to valid range
        quantized = np.clip(quantized, -1.0, 1.0)

        return cast(np.ndarray, quantized.astype(np.float32))

    def get_params(self) -> dict[str, Any]:
        return {"cutoff_hz": self.cutoff_hz, "bits": self.bits, "seed": self.seed}


class PitchShiftPerturbation(Perturbation):
    """
    Pitch shift stub using resampling approximation.

    NOTE: This is NOT a true pitch shift (which would preserve duration).
    It's a simple resampling approximation for testing indicator robustness
    to frequency shifts. For true pitch shifting, integrate librosa or similar.
    """

    def __init__(self, semitones: float | None = None, seed: int = 1337):
        super().__init__("pitch_shift", seed)
        # Load from config if not provided
        if semitones is None:
            defaults = get_perturbation_defaults("pitch_shift")
            semitones = defaults.get("semitones", 2.0)
        # Validate semitones to prevent extreme values
        if not -24 <= semitones <= 24:
            raise ValueError(
                f"semitones must be in range [-24, 24], got {semitones}. "
                "Use librosa or similar for larger pitch shifts."
            )
        self.semitones = semitones

    def apply(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Pitch shift using librosa.effects.pitch_shift.

        This preserves duration while shifting pitch.
        """
        # Convert to float32 for librosa
        audio_float = audio.astype(np.float32)

        # Apply pitch shift
        shifted = librosa.effects.pitch_shift(
            y=audio_float,
            sr=sample_rate,
            n_steps=self.semitones,
            res_type="kaiser_fast",
        )

        # Pad or trim to original length if needed (though librosa should preserve it)
        if len(shifted) < len(audio):
            padded = np.zeros_like(audio)
            padded[: len(shifted)] = shifted
            result = padded
        elif len(shifted) > len(audio):
            result = shifted[: len(audio)]
        else:
            result = shifted

        # Clip to valid range
        result = np.clip(result, -1.0, 1.0)

        return result

    def get_params(self) -> dict[str, Any]:
        return {"semitones": self.semitones, "seed": self.seed}


class TimeStretchPerturbation(Perturbation):
    """
    Time stretch stub using decimation/interpolation approximation.

    NOTE: This is NOT a true time stretch (which would preserve pitch).
    It's a simple resampling approximation for testing indicator robustness
    to temporal changes. For true time stretching, integrate librosa or rubberband.
    """

    def __init__(self, rate: float | None = None, seed: int = 1337):
        super().__init__("time_stretch", seed)
        # Load from config if not provided
        if rate is None:
            defaults = get_perturbation_defaults("time_stretch")
            rate = defaults.get("rate", 1.2)
        # Validate rate to prevent extreme values and division by zero
        if not 0.25 <= rate <= 4.0:
            raise ValueError(
                f"rate must be in range [0.25, 4.0], got {rate}. "
                "Use librosa or rubberband for more extreme time stretching."
            )
        self.rate = rate

    def apply(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Time stretch using librosa.effects.time_stretch.

        This preserves pitch while shifting duration.
        """
        # Convert to float32 for librosa
        audio_float = audio.astype(np.float32)

        # Apply time stretch
        # librosa 0.10+ uses time_stretch directly
        stretched = librosa.effects.time_stretch(y=audio_float, rate=self.rate)

        # Pad or trim to original length to maintain compatibility for slice processing
        if len(stretched) < len(audio):
            padded = np.zeros_like(audio)
            padded[: len(stretched)] = stretched
            result = padded
        else:
            result = stretched[: len(audio)]

        # Clip to valid range
        result = np.clip(result, -1.0, 1.0)

        return result

    def get_params(self) -> dict[str, Any]:
        return {"rate": self.rate, "seed": self.seed}


class RealCodecPerturbation(Perturbation):
    """Real codec integration using pydub/ffmpeg."""

    def __init__(self, format: str = "mp3", bitrate: str | None = None, seed: int = 1337):
        super().__init__(f"codec_{format}", seed)
        self.format = format
        # Load from config if not provided
        if bitrate is None:
            defaults = get_perturbation_defaults(format)
            bitrate = defaults.get("bitrate", "64k")
        self.bitrate = bitrate

    def apply(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Encode and decode audio using specified codec and bitrate."""
        # Convert numpy to pydub AudioSegment
        # Multiplied by 32767 for 16-bit PCM scale
        audio_int16 = (audio * 32767).astype(np.int16)
        segment = AudioSegment(
            audio_int16.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=1,
        )

        # Use temporary file to simulate codec pass
        with tempfile.NamedTemporaryFile(suffix=f".{self.format}", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Export to codec format
            segment.export(tmp_path, format=self.format, bitrate=self.bitrate)

            # Load back
            encoded_segment = AudioSegment.from_file(tmp_path, format=self.format)

            # Ensure same sample rate and mono
            encoded_segment = encoded_segment.set_frame_rate(sample_rate).set_channels(1)

            # Convert back to numpy
            samples = np.array(encoded_segment.get_array_of_samples()).astype(np.float32) / 32767.0

            # Pad or trim to original length
            if len(samples) < len(audio):
                padded = np.zeros_like(audio)
                padded[: len(samples)] = samples
                result = padded
            else:
                result = samples[: len(audio)]

            return result

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def get_params(self) -> dict[str, Any]:
        return {"format": self.format, "bitrate": self.bitrate, "seed": self.seed}


def get_perturbation(name: str, seed: int = 1337, **kwargs) -> Perturbation:
    """
    Factory function to create perturbations.

    Args:
        name: Perturbation name ('none', 'noise', 'codec_stub', 'pitch_shift', 'time_stretch')
        seed: Random seed for deterministic behavior
        **kwargs: Additional parameters for specific perturbations.
                 If not provided, loads from config files.

    Returns:
        Perturbation instance

    Raises:
        ValueError: If perturbation name is unknown
    """
    if name == "none":
        return NonePerturbation(seed=seed)
    elif name == "noise":
        snr_db = kwargs.get("snr_db")
        return NoisePerturbation(snr_db=snr_db, seed=seed)
    elif name == "codec_stub":
        cutoff_hz = kwargs.get("cutoff_hz")
        bits = kwargs.get("bits")
        return CodecStubPerturbation(cutoff_hz=cutoff_hz, bits=bits, seed=seed)
    elif name == "pitch_shift":
        semitones = kwargs.get("semitones")
        return PitchShiftPerturbation(semitones=semitones, seed=seed)
    elif name == "time_stretch":
        rate = kwargs.get("rate")
        return TimeStretchPerturbation(rate=rate, seed=seed)
    elif name == "opus":
        bitrate = kwargs.get("bitrate")
        # Use ogg as container for opus
        return RealCodecPerturbation(format="ogg", bitrate=bitrate, seed=seed)
    elif name == "mp3":
        bitrate = kwargs.get("bitrate")
        return RealCodecPerturbation(format="mp3", bitrate=bitrate, seed=seed)
    else:
        raise ValueError(f"Unknown perturbation: {name}")
