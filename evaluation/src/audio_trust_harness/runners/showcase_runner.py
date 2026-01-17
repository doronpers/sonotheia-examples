"""
Showcase runner for deterministic, public-safe evaluation.

Demonstrates Sonotheia's evidence-first voice risk assessment
with synthetic fixtures and audit-ready JSONL output.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from audio_trust_harness.audit.record import (
    AuditRecord,
    DeferralInfo,
    write_audit_record,
)
from audio_trust_harness.audit.sanitize import sanitize_audit_record
from audio_trust_harness.sensors import InteractionalSensor, UnknownSensor


class ShowcaseRunner:
    """Runner for showcasing evidence-first voice risk assessment.

    Processes audio through public-safe sensors and emits audit JSONL
    records with signals, confidence, reason_codes, and recommended_action.
    """

    def __init__(self):
        """Initialize the showcase runner."""
        self.interactional_sensor = InteractionalSensor()
        self.unknown_sensor = UnknownSensor()

    def run(
        self,
        fixture_name: str,
        output_path: Path,
        sample_rate: int = 16000,
        deterministic: bool = True,
    ) -> None:
        """Run showcase evaluation on a synthetic fixture.

        Args:
            fixture_name: Name of the synthetic fixture to generate
            output_path: Path to output JSONL file
            sample_rate: Sample rate in Hz (default: 16000)
            deterministic: If True, use fixed timestamps for byte-for-byte determinism

        Raises:
            ValueError: If fixture_name is not recognized
            FileNotFoundError: If output directory doesn't exist
        """
        # Generate synthetic audio fixture
        audio = self._generate_fixture(fixture_name, sample_rate)

        # Process through sensors
        interactional_result = self.interactional_sensor.analyze(
            audio, sample_rate
        )
        unknown_result = self.unknown_sensor.analyze(audio, sample_rate)

        # Combine results
        combined_signals = {
            **{
                f"interactional_{k}": v
                for k, v in interactional_result.signals.items()
            },
            **{f"unknown_{k}": v for k, v in unknown_result.signals.items()},
        }

        # Aggregate confidence (weighted average)
        confidence = (
            interactional_result.confidence * 0.5
            + unknown_result.confidence * 0.5
        )

        # Combine reason codes
        reason_codes = (
            interactional_result.reason_codes + unknown_result.reason_codes
        )

        # Determine overall action (most conservative)
        actions = [
            interactional_result.recommended_action,
            unknown_result.recommended_action,
        ]
        if "insufficient_evidence" in actions:
            recommended_action = "insufficient_evidence"
        elif "defer_to_review" in actions:
            recommended_action = "defer_to_review"
        else:
            recommended_action = "accept"

        # Create audit record
        record = self._create_showcase_record(
            fixture_name=fixture_name,
            signals=combined_signals,
            confidence=confidence,
            reason_codes=reason_codes,
            recommended_action=recommended_action,
            sample_rate=sample_rate,
            duration_s=len(audio) / sample_rate,
            deterministic=deterministic,
        )

        # Sanitize record to ensure no forbidden fields
        record_dict = record.model_dump()
        sanitized_dict = sanitize_audit_record(record_dict)

        # Write sanitized record to JSONL
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "a") as f:
            f.write(json.dumps(sanitized_dict, sort_keys=True) + "\n")

    def _generate_fixture(
        self, fixture_name: str, sample_rate: int, seed: int = 42
    ) -> np.ndarray:
        """Generate synthetic audio fixture.

        Args:
            fixture_name: Name of fixture to generate
            sample_rate: Sample rate in Hz
            seed: Random seed for deterministic generation (default: 42)

        Returns:
            Audio samples as float32 numpy array

        Raises:
            ValueError: If fixture_name is not recognized
        """
        # Set seed for deterministic generation
        np.random.seed(seed)

        duration_sec = 2.0
        n_samples = int(duration_sec * sample_rate)
        t = np.arange(n_samples) / sample_rate

        if fixture_name == "clean_speech":
            # Multi-harmonic speech-like signal
            f0 = 120 + 20 * np.sin(2 * np.pi * 3 * t)
            audio = np.zeros(n_samples, dtype=np.float32)
            for harmonic in [1, 2, 3, 4, 5]:
                amplitude = 1.0 / harmonic
                audio += amplitude * np.sin(2 * np.pi * f0 * harmonic * t)
            audio += np.random.normal(0, 0.01, n_samples).astype(
                np.float32
            )
            audio = audio / np.max(np.abs(audio)) * 0.7

        elif fixture_name == "noisy_speech":
            # Speech with ambient noise
            f0 = 120 + 20 * np.sin(2 * np.pi * 3 * t)
            audio = np.zeros(n_samples, dtype=np.float32)
            for harmonic in [1, 2, 3, 4, 5]:
                amplitude = 1.0 / harmonic
                audio += amplitude * np.sin(2 * np.pi * f0 * harmonic * t)
            # Add significant noise
            audio += np.random.normal(0, 0.15, n_samples).astype(np.float32)
            audio = audio / np.max(np.abs(audio)) * 0.7

        elif fixture_name == "tone":
            # Simple tone
            audio = 0.5 * np.sin(2 * np.pi * 440 * t).astype(np.float32)

        elif fixture_name == "noise":
            # White noise
            audio = np.random.normal(0, 0.3, n_samples).astype(np.float32)
            audio = audio / np.max(np.abs(audio)) * 0.7

        elif fixture_name == "turntaking_normal":
            # Normal turn-taking pattern: alternating speech segments with pauses
            audio = np.zeros(n_samples, dtype=np.float32)
            # Create 4 alternating segments
            segment_duration = duration_sec / 4
            segment_samples = int(segment_duration * sample_rate)
            for i in range(4):
                start_idx = i * segment_samples
                end_idx = min(start_idx + segment_samples, n_samples)
                if i % 2 == 0:  # Speech segment
                    f0 = 150 + 30 * np.sin(2 * np.pi * 2 * t[start_idx:end_idx])
                    segment = np.zeros(end_idx - start_idx, dtype=np.float32)
                    for harmonic in [1, 2, 3]:
                        amplitude = 1.0 / harmonic
                        segment += amplitude * np.sin(
                            2 * np.pi * f0 * harmonic * t[start_idx:end_idx]
                        )
                    audio[start_idx:end_idx] = segment
                # Odd segments are silence (already zero)
            audio = audio / (np.max(np.abs(audio)) + 1e-10) * 0.7

        elif fixture_name == "turntaking_anomalous":
            # Anomalous turn-taking: overlapping speech, no pauses
            audio = np.zeros(n_samples, dtype=np.float32)
            # Create overlapping speech segments
            segment_duration = duration_sec / 3
            segment_samples = int(segment_duration * sample_rate)
            for i in range(3):
                start_idx = max(0, i * segment_samples - segment_samples // 2)
                end_idx = min(start_idx + segment_samples, n_samples)
                f0 = 140 + 40 * np.sin(2 * np.pi * 2.5 * t[start_idx:end_idx])
                segment = np.zeros(end_idx - start_idx, dtype=np.float32)
                for harmonic in [1, 2, 3]:
                    amplitude = 0.8 / harmonic
                    segment += amplitude * np.sin(
                        2 * np.pi * f0 * harmonic * t[start_idx:end_idx]
                    )
                audio[start_idx:end_idx] += segment
            audio = audio / (np.max(np.abs(audio)) + 1e-10) * 0.7

        elif fixture_name == "overlap_high":
            # High overlap: multiple simultaneous speakers
            audio = np.zeros(n_samples, dtype=np.float32)
            # Create 3 simultaneous speech signals
            for speaker in range(3):
                f0_base = 120 + speaker * 30
                f0 = f0_base + 20 * np.sin(2 * np.pi * (2 + speaker) * t)
                speaker_audio = np.zeros(n_samples, dtype=np.float32)
                for harmonic in [1, 2, 3]:
                    amplitude = 0.6 / harmonic
                    speaker_audio += amplitude * np.sin(
                        2 * np.pi * f0 * harmonic * t
                    )
                audio += speaker_audio
            audio = audio / (np.max(np.abs(audio)) + 1e-10) * 0.7

        else:
            raise ValueError(
                f"Unknown fixture: {fixture_name}. "
                f"Valid options: clean_speech, noisy_speech, tone, noise, "
                f"turntaking_normal, turntaking_anomalous, overlap_high"
            )

        return audio.astype(np.float32)

    def _create_showcase_record(
        self,
        fixture_name: str,
        signals: dict[str, float],
        confidence: float,
        reason_codes: list[str],
        recommended_action: str,
        sample_rate: int,
        duration_s: float,
        deterministic: bool = True,
    ) -> AuditRecord:
        """Create audit record for showcase evaluation.

        Args:
            fixture_name: Name of fixture used
            signals: Combined signal values from all sensors
            confidence: Aggregated confidence score
            reason_codes: Combined reason codes
            recommended_action: Recommended action
            sample_rate: Sample rate in Hz
            duration_s: Duration in seconds
            deterministic: If True, use fixed timestamps for determinism

        Returns:
            AuditRecord instance
        """
        import sys

        # For deterministic output, use fixed timestamp and run_id
        if deterministic:
            # Fixed timestamp for byte-for-byte determinism
            timestamp = "2026-01-01T00:00:00.000000"
            run_id = f"showcase_{fixture_name}_deterministic"
        else:
            timestamp = datetime.now().isoformat()
            import uuid

            run_id = (
                f"showcase_{datetime.now().strftime('%Y%m%d_%H%M%S')}_"
                f"{uuid.uuid4().hex[:6]}"
            )

        # Ensure confidence is in bounds
        confidence = max(0.0, min(1.0, confidence))

        # Create a record that includes all required fields
        return AuditRecord(
            run_id=run_id,
            timestamp=timestamp,
            tool_version="0.1.0",
            git_sha="showcase_deterministic",
            python_version=sys.version.split()[0],
            input_file=f"fixture_{fixture_name}.wav",
            sample_rate=sample_rate,
            slice_index=0,
            slice_start_s=0.0,
            slice_duration_s=duration_s,
            perturbation_name="none",
            perturbation_params={},
            indicators=signals,  # Signals go in indicators field
            deferral=DeferralInfo(
                recommended_action=recommended_action,
                fragility_score=1.0 - confidence,  # Convert confidence to fragility
                reasons=sorted(reason_codes),  # Sort for determinism
            ),
            warnings=[],
        )
