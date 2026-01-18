#!/usr/bin/env python3
"""
Generate test audio files for Sonotheia API testing (No ffmpeg required).

This script creates synthetic audio files for testing using pure Python.
All files are generated using the wave module without external dependencies.
"""

import math
import random
import struct
import wave
from pathlib import Path


def generate_silent(filename: str, duration_seconds: int, sample_rate: int = 16000) -> None:
    """Generate silent audio file."""
    num_samples = sample_rate * duration_seconds
    with wave.open(filename, "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        # Write zeros for silence
        wav_file.writeframes(b"\x00\x00" * num_samples)
    print(f"✓ Created {filename}")


def generate_tone(
    filename: str, frequency: float, duration_seconds: int, sample_rate: int = 16000
) -> None:
    """Generate sine wave tone audio file."""
    num_samples = sample_rate * duration_seconds
    with wave.open(filename, "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # Generate sine wave
        amplitude = 16384  # Half of max 16-bit value for safety
        for i in range(num_samples):
            value = int(amplitude * math.sin(2 * math.pi * frequency * i / sample_rate))
            wav_file.writeframes(struct.pack("<h", value))
    print(f"✓ Created {filename}")


def generate_stereo(filename: str, duration_seconds: int, sample_rate: int = 16000) -> None:
    """Generate stereo silent audio file."""
    num_samples = sample_rate * duration_seconds
    with wave.open(filename, "w") as wav_file:
        wav_file.setnchannels(2)  # Stereo
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        # Write zeros for both channels
        wav_file.writeframes(b"\x00\x00\x00\x00" * num_samples)
    print(f"✓ Created {filename}")


def generate_white_noise(filename: str, duration_seconds: int, sample_rate: int = 16000) -> None:
    """Generate white noise audio file."""
    num_samples = sample_rate * duration_seconds
    with wave.open(filename, "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # Generate white noise (random values)
        amplitude = 8192  # Quarter of max 16-bit value
        for _ in range(num_samples):
            value = int(amplitude * (2 * random.random() - 1))
            wav_file.writeframes(struct.pack("<h", value))
    print(f"✓ Created {filename}")


def generate_pink_noise(filename: str, duration_seconds: int, sample_rate: int = 16000) -> None:
    """Generate pink noise audio file (approximation)."""
    num_samples = sample_rate * duration_seconds
    with wave.open(filename, "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # Simple pink noise approximation using cascaded filters
        b = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        amplitude = 8192

        for _ in range(num_samples):
            white = 2 * random.random() - 1
            b[0] = 0.99886 * b[0] + white * 0.0555179
            b[1] = 0.99332 * b[1] + white * 0.0750759
            b[2] = 0.96900 * b[2] + white * 0.1538520
            b[3] = 0.86650 * b[3] + white * 0.3104856
            b[4] = 0.55000 * b[4] + white * 0.5329522
            b[5] = -0.7616 * b[5] - white * 0.0168980
            pink = b[0] + b[1] + b[2] + b[3] + b[4] + b[5] + b[6] + white * 0.5362
            b[6] = white * 0.115926

            value = int(amplitude * pink * 0.11)
            value = max(-32768, min(32767, value))  # Clip to 16-bit range
            wav_file.writeframes(struct.pack("<h", value))
    print(f"✓ Created {filename}")


def main():
    """Generate all test audio files."""
    print("Generating test audio files (no ffmpeg required)...")
    print()

    # Basic test files
    print("Basic test files:")
    generate_silent("silent_5s.wav", 5)
    generate_silent("silent_10s.wav", 10)
    generate_silent("silent_3s.wav", 3)
    generate_tone("tone_440hz_5s.wav", 440, 5)
    generate_tone("tone_440hz_10s.wav", 440, 10)
    print()

    # Edge case files
    print("Edge case files:")
    generate_silent("short_1s.wav", 1)
    generate_silent("long_30s.wav", 30)
    generate_stereo("stereo_5s.wav", 5)
    generate_silent("8khz_5s.wav", 5, sample_rate=8000)
    generate_silent("48khz_5s.wav", 5, sample_rate=48000)
    print()

    # Noise files
    print("Noise files:")
    generate_white_noise("white_noise_5s.wav", 5)
    generate_pink_noise("pink_noise_5s.wav", 5)
    print()

    print("✓ All test audio files generated successfully!")
    print()
    print("Files created:")
    for wav_file in sorted(Path(".").glob("*.wav")):
        if wav_file.name not in ["generate_test_audio.py"]:
            size_kb = wav_file.stat().st_size / 1024
            print(f"  - {wav_file.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
