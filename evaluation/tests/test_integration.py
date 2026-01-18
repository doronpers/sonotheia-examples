"""Integration tests for CLI."""

import json

import numpy as np
import pytest
import soundfile as sf
from typer.testing import CliRunner

from audio_trust_harness.cli import app

runner = CliRunner()


@pytest.fixture
def test_audio_file(tmp_path):
    """Create a test WAV file."""
    # Generate 15 seconds of audio (440Hz sine + some noise)
    sr = 16000
    duration = 15.0
    t = np.linspace(0, duration, int(sr * duration))
    audio = 0.3 * np.sin(2 * np.pi * 440 * t) + 0.1 * np.random.randn(len(t))

    wav_path = tmp_path / "test_audio.wav"
    sf.write(wav_path, audio, sr)

    return wav_path


def test_cli_run_basic(test_audio_file, tmp_path):
    """Test basic CLI run command produces audit.jsonl."""
    out_file = tmp_path / "audit.jsonl"

    result = runner.invoke(
        app,
        [
            "run",
            str(test_audio_file),
            "--out",
            str(out_file),
            "--slice-seconds",
            "10",
            "--hop-seconds",
            "10",
            "--seed",
            "1337",
            "--perturbations",
            "none,noise",
        ],
    )

    # Check command succeeded
    assert result.exit_code == 0, f"CLI failed with: {result.stdout}"

    # Check output file exists
    assert out_file.exists()

    # Check output file is not empty
    assert out_file.stat().st_size > 0

    # Check JSONL format
    records = []
    with open(out_file) as f:
        for line in f:
            record = json.loads(line)
            records.append(record)

    # Should have records (1 slice * 2 perturbations = 2 records)
    assert len(records) >= 2

    # Check record structure
    first_record = records[0]
    required_fields = [
        "run_id",
        "timestamp",
        "tool_version",
        "python_version",
        "input_file",
        "sample_rate",
        "slice_index",
        "slice_start_s",
        "slice_duration_s",
        "perturbation_name",
        "perturbation_params",
        "indicators",
        "deferral",
        "warnings",
    ]

    for field in required_fields:
        assert field in first_record, f"Missing field: {field}"

    # Check deferral structure
    deferral = first_record["deferral"]
    assert "recommended_action" in deferral
    assert "fragility_score" in deferral
    assert "reasons" in deferral

    # Check action is one of the three valid values
    assert deferral["recommended_action"] in [
        "accept",
        "defer_to_review",
        "insufficient_evidence",
    ]


def test_cli_run_with_max_slices(test_audio_file, tmp_path):
    """Test CLI run with max_slices limit."""
    out_file = tmp_path / "audit.jsonl"

    result = runner.invoke(
        app,
        [
            "run",
            str(test_audio_file),
            "--out",
            str(out_file),
            "--slice-seconds",
            "5",
            "--hop-seconds",
            "5",
            "--max-slices",
            "2",
            "--perturbations",
            "none",
        ],
    )

    assert result.exit_code == 0

    # Count records
    with open(out_file) as f:
        records = [json.loads(line) for line in f]

    # Should have exactly 2 slices * 1 perturbation = 2 records
    assert len(records) == 2


def test_cli_run_multiple_perturbations(test_audio_file, tmp_path):
    """Test CLI run with multiple perturbations."""
    out_file = tmp_path / "audit.jsonl"

    result = runner.invoke(
        app,
        [
            "run",
            str(test_audio_file),
            "--out",
            str(out_file),
            "--slice-seconds",
            "10",
            "--hop-seconds",
            "10",
            "--max-slices",
            "1",
            "--perturbations",
            "none,noise,codec_stub",
        ],
    )

    assert result.exit_code == 0

    # Count records
    with open(out_file) as f:
        records = [json.loads(line) for line in f]

    # Should have 1 slice * 3 perturbations = 3 records
    assert len(records) == 3

    # Check all perturbations present
    perturbations = {r["perturbation_name"] for r in records}
    assert perturbations == {"none", "noise", "codec_stub"}


def test_cli_run_file_not_found(tmp_path):
    """Test CLI run with non-existent file."""
    out_file = tmp_path / "audit.jsonl"

    result = runner.invoke(
        app,
        [
            "run",
            "nonexistent.wav",
            "--out",
            str(out_file),
        ],
    )

    # Should fail
    assert result.exit_code != 0


def test_cli_version():
    """Test CLI version command."""
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "Audio Trust Harness" in result.stdout
    assert "v0.1.0" in result.stdout


def test_cli_deterministic_with_seed(test_audio_file, tmp_path):
    """Test that CLI produces identical results with same seed."""
    out_file1 = tmp_path / "audit1.jsonl"
    out_file2 = tmp_path / "audit2.jsonl"

    # Run 1
    result1 = runner.invoke(
        app,
        [
            "run",
            str(test_audio_file),
            "--out",
            str(out_file1),
            "--seed",
            "42",
            "--perturbations",
            "noise",
            "--max-slices",
            "1",
        ],
    )

    # Run 2 (same seed)
    result2 = runner.invoke(
        app,
        [
            "run",
            str(test_audio_file),
            "--out",
            str(out_file2),
            "--seed",
            "42",
            "--perturbations",
            "noise",
            "--max-slices",
            "1",
        ],
    )

    assert result1.exit_code == 0
    assert result2.exit_code == 0

    # Compare indicators (should be identical with same seed)
    with open(out_file1) as f:
        records1 = [json.loads(line) for line in f]

    with open(out_file2) as f:
        records2 = [json.loads(line) for line in f]

    # Compare indicator values (should be very close)
    indicators1 = records1[0]["indicators"]
    indicators2 = records2[0]["indicators"]

    for key in indicators1:
        assert abs(indicators1[key] - indicators2[key]) < 1e-6
