"""
Tests for showcase runner.

Tests determinism, bounds, and sanitation requirements.
"""

import json

import numpy as np
import pytest

from audio_trust_harness.runners import ShowcaseRunner
from audio_trust_harness.sensors import InteractionalSensor, UnknownSensor


class TestShowcaseDeterminism:
    """Test determinism of showcase runner."""

    def test_same_fixture_twice_produces_same_output(self, tmp_path):
        """Test that same fixture produces identical output twice (byte-for-byte)."""
        runner = ShowcaseRunner()
        fixture_name = "clean_speech"
        output1 = tmp_path / "output1.jsonl"
        output2 = tmp_path / "output2.jsonl"

        # Run twice with deterministic mode
        runner.run(fixture_name=fixture_name, output_path=output1, deterministic=True)
        runner.run(fixture_name=fixture_name, output_path=output2, deterministic=True)

        # Read both outputs as raw bytes for byte-for-byte comparison
        with open(output1, "rb") as f:
            content1 = f.read()
        with open(output2, "rb") as f:
            content2 = f.read()

        # Byte-for-byte identical
        assert content1 == content2, "Outputs should be byte-for-byte identical"

        # Also verify JSON structure
        record1 = json.loads(content1.decode())
        record2 = json.loads(content2.decode())

        # Compare key fields
        assert record1["indicators"] == record2["indicators"]
        assert record1["deferral"]["fragility_score"] == record2["deferral"]["fragility_score"]
        assert (
            record1["deferral"]["recommended_action"] == record2["deferral"]["recommended_action"]
        )
        assert record1["deferral"]["reasons"] == record2["deferral"]["reasons"]

    def test_different_fixtures_produce_different_output(self, tmp_path):
        """Test that different fixtures produce different output."""
        runner = ShowcaseRunner()
        output1 = tmp_path / "output1.jsonl"
        output2 = tmp_path / "output2.jsonl"

        runner.run(fixture_name="clean_speech", output_path=output1, deterministic=True)
        runner.run(fixture_name="noise", output_path=output2, deterministic=True)

        # Read both outputs
        with open(output1) as f:
            record1 = json.loads(f.readline())
        with open(output2) as f:
            record2 = json.loads(f.readline())

        # Should have different indicators
        assert record1["indicators"] != record2["indicators"]

    def test_new_fixtures_work(self, tmp_path):
        """Test that new fixtures (turntaking_normal, turntaking_anomalous, overlap_high) work."""
        runner = ShowcaseRunner()
        fixtures = ["turntaking_normal", "turntaking_anomalous", "overlap_high"]

        for fixture_name in fixtures:
            output = tmp_path / f"{fixture_name}.jsonl"
            runner.run(fixture_name=fixture_name, output_path=output, deterministic=True)

            # Verify output is valid JSONL
            with open(output) as f:
                record = json.loads(f.readline())

            assert "indicators" in record
            assert "deferral" in record
            assert record["deferral"]["recommended_action"] in [
                "accept",
                "defer_to_review",
                "insufficient_evidence",
            ]


class TestShowcaseBounds:
    """Test bounds constraints."""

    def test_confidence_in_bounds(self, tmp_path):
        """Test that confidence is always in [0.0, 1.0]."""
        runner = ShowcaseRunner()
        fixtures = [
            "clean_speech",
            "noisy_speech",
            "tone",
            "noise",
            "turntaking_normal",
            "turntaking_anomalous",
            "overlap_high",
        ]

        for fixture_name in fixtures:
            output = tmp_path / f"{fixture_name}.jsonl"
            runner.run(fixture_name=fixture_name, output_path=output, deterministic=True)

            with open(output) as f:
                record = json.loads(f.readline())

            # Confidence should be in bounds
            # We compute confidence from fragility_score: confidence = 1.0 - fragility_score
            fragility = record["deferral"]["fragility_score"]
            confidence = 1.0 - fragility

            assert (
                0.0 <= confidence <= 1.0
            ), f"Confidence {confidence} out of bounds for fixture {fixture_name}"

            # Fragility score should also be in reasonable bounds (0.0 to 1.0 typically)
            assert (
                0.0 <= fragility <= 1.0
            ), f"Fragility {fragility} out of bounds for fixture {fixture_name}"

    def test_all_signals_are_numeric(self, tmp_path):
        """Test that all signal values are numeric."""
        runner = ShowcaseRunner()
        output = tmp_path / "output.jsonl"
        runner.run(fixture_name="clean_speech", output_path=output, deterministic=True)

        with open(output) as f:
            record = json.loads(f.readline())

        # All indicators should be numeric
        for key, value in record["indicators"].items():
            assert isinstance(
                value, (int, float)
            ), f"Signal {key} has non-numeric value: {type(value)}"


class TestShowcaseSanitation:
    """Test sanitation (no raw audio bytes, no base64)."""

    def test_no_raw_audio_bytes(self, tmp_path):
        """Test that output contains no raw audio bytes."""
        from audio_trust_harness.audit.sanitize import validate_no_forbidden_fields

        runner = ShowcaseRunner()
        output = tmp_path / "output.jsonl"
        runner.run(fixture_name="clean_speech", output_path=output, deterministic=True)

        with open(output) as f:
            content = f.read()

        # Check for common byte patterns
        # Raw audio would typically be large arrays or base64
        assert "base64" not in content.lower()
        assert "bytes" not in content.lower()
        assert "audio_data" not in content.lower()
        assert "raw_audio" not in content.lower()

        # Validate using sanitize module
        record = json.loads(content)
        assert validate_no_forbidden_fields(record), "Record contains forbidden fields"

    def test_no_base64_fields(self, tmp_path):
        """Test that output contains no base64-encoded fields."""
        from audio_trust_harness.audit.sanitize import is_base64_like

        runner = ShowcaseRunner()
        output = tmp_path / "output.jsonl"
        runner.run(fixture_name="clean_speech", output_path=output, deterministic=True)

        with open(output) as f:
            record = json.loads(f.readline())

        # Recursively check all values for base64-like strings
        def check_for_base64(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    check_for_base64(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    check_for_base64(v, f"{path}[{i}]")
            elif isinstance(obj, str):
                if is_base64_like(obj):
                    pytest.fail(f"Potential base64 field found at {path}: {obj[:50]}...")

        check_for_base64(record)

    def test_output_is_valid_jsonl(self, tmp_path):
        """Test that output is valid JSONL format."""
        runner = ShowcaseRunner()
        output = tmp_path / "output.jsonl"
        runner.run(fixture_name="clean_speech", output_path=output, deterministic=True)

        # Should be readable as JSONL
        with open(output) as f:
            lines = f.readlines()

        assert len(lines) == 1, "Should have exactly one line"

        # Should be valid JSON
        record = json.loads(lines[0])
        assert isinstance(record, dict)
        assert "indicators" in record
        assert "deferral" in record

    def test_fast_runtime(self, tmp_path):
        """Test that showcase runner completes in <2 seconds."""
        import time

        runner = ShowcaseRunner()
        output = tmp_path / "output.jsonl"
        fixtures = ["turntaking_normal", "turntaking_anomalous", "overlap_high"]

        for fixture_name in fixtures:
            start_time = time.time()
            runner.run(fixture_name=fixture_name, output_path=output, deterministic=True)
            elapsed = time.time() - start_time
            assert elapsed < 2.0, f"Fixture {fixture_name} took {elapsed:.2f}s (should be <2s)"


class TestShowcaseSensors:
    """Test individual sensors."""

    def test_interactional_sensor_bounds(self):
        """Test that interactional sensor produces valid results."""
        sensor = InteractionalSensor()
        audio = np.random.randn(16000).astype(np.float32) * 0.1

        result = sensor.analyze(audio, sample_rate=16000)

        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.signals, dict)
        assert isinstance(result.reason_codes, list)
        assert result.recommended_action in [
            "accept",
            "defer_to_review",
            "insufficient_evidence",
        ]

    def test_unknown_sensor_bounds(self):
        """Test that unknown sensor produces valid results."""
        sensor = UnknownSensor()
        audio = np.random.randn(16000).astype(np.float32) * 0.1

        result = sensor.analyze(audio, sample_rate=16000)

        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.signals, dict)
        assert isinstance(result.reason_codes, list)
        assert result.recommended_action in [
            "accept",
            "defer_to_review",
            "insufficient_evidence",
        ]

    def test_sensors_handle_empty_audio(self):
        """Test that sensors handle empty audio gracefully."""
        interactional = InteractionalSensor()
        unknown = UnknownSensor()

        empty_audio = np.array([], dtype=np.float32)

        result1 = interactional.analyze(empty_audio, sample_rate=16000)
        result2 = unknown.analyze(empty_audio, sample_rate=16000)

        assert result1.confidence == 0.0
        assert result2.confidence == 0.0
        assert result1.recommended_action == "insufficient_evidence"
        assert result2.recommended_action == "insufficient_evidence"

    def test_sensors_handle_short_audio(self):
        """Test that sensors handle short audio gracefully."""
        interactional = InteractionalSensor()
        unknown = UnknownSensor()

        # Less than 0.5 seconds
        short_audio = np.random.randn(4000).astype(np.float32) * 0.1

        result1 = interactional.analyze(short_audio, sample_rate=16000)
        result2 = unknown.analyze(short_audio, sample_rate=16000)

        assert 0.0 <= result1.confidence <= 1.0
        assert 0.0 <= result2.confidence <= 1.0
        assert "AUDIO_TOO_SHORT" in result1.reason_codes
        assert "AUDIO_TOO_SHORT" in result2.reason_codes


class TestShowcaseFixtures:
    """Test fixture generation."""

    def test_all_fixtures_generate_valid_audio(self):
        """Test that all fixtures generate valid audio."""
        runner = ShowcaseRunner()
        fixtures = [
            "clean_speech",
            "noisy_speech",
            "tone",
            "noise",
            "turntaking_normal",
            "turntaking_anomalous",
            "overlap_high",
        ]

        for fixture_name in fixtures:
            audio = runner._generate_fixture(fixture_name, sample_rate=16000)

            assert isinstance(audio, np.ndarray)
            assert audio.dtype == np.float32
            assert len(audio) > 0
            assert np.all(np.isfinite(audio))

    def test_invalid_fixture_raises_error(self):
        """Test that invalid fixture name raises error."""
        runner = ShowcaseRunner()

        with pytest.raises(ValueError, match="Unknown fixture"):
            runner._generate_fixture("invalid_fixture", sample_rate=16000)
