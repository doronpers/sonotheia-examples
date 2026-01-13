#!/usr/bin/env python3
"""
Generate synthetic demo audio files for audio-trust-harness.
This avoids storing binary blobs in the repository.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import soundfile as sf


def generate_tone(duration_s=10.0, freq_hz=440.0, sr=16000, amplitude=0.5):
    """Generate a pure sine wave."""
    t = np.linspace(0, duration_s, int(sr * duration_s), endpoint=False)
    audio = amplitude * np.sin(2 * np.pi * freq_hz * t)
    return audio


def generate_noise(duration_s=10.0, sr=16000, amplitude=0.1):
    """Generate white noise."""
    samples = int(sr * duration_s)
    rng = np.random.default_rng(42)  # Fixed seed for reproducibility
    audio = rng.uniform(-amplitude, amplitude, samples)
    return audio


def generate_clipped(duration_s=10.0, sr=16000):
    """Generate heavily clipped audio (sine wave > 1.0)."""
    # Generate 1.5 amplitude sine, then clip to 1.0
    raw = generate_tone(duration_s, 440.0, sr, amplitude=1.5)
    return np.clip(
        raw, -0.99, 0.99
    )  # soundfile might clip automatically, but let's be explicit


def main():
    parser = argparse.ArgumentParser(description="Generate demo audio files")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("examples/test-audio"),
        help="Output directory",
    )
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating demo audio in {out_dir}...")

    # 1. Clean Speech Proxy (Pure Tone for stability)
    # Using a Tone instead of TTS to avoid external deps/model weights
    sf.write(out_dir / "clean_tone.wav", generate_tone(10.0), 16000)
    print("✓ Created clean_tone.wav")

    # 2. Noisy Signal
    clean = generate_tone(10.0)
    noise = generate_noise(10.0, amplitude=0.1)
    noisy = clean + noise
    sf.write(out_dir / "noisy_tone.wav", noisy, 16000)
    print("✓ Created noisy_tone.wav")

    # 3. Clipped Signal
    sf.write(out_dir / "clipped.wav", generate_clipped(10.0), 16000)
    print("✓ Created clipped.wav")

    # 4. Too Short
    sf.write(out_dir / "too_short.wav", generate_tone(0.2), 16000)
    print("✓ Created too_short.wav")

    print(f"\nDone! Generated {len(list(out_dir.glob('*.wav')))} files.")


if __name__ == "__main__":
    main()
