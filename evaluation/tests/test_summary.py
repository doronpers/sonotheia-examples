"""
Tests for summary report generation.
"""

import json

import pytest

from audio_trust_harness.audit.summary import (
    compute_summary,
    generate_summary_report,
    load_audit_records,
    write_summary,
)


@pytest.fixture
def sample_audit_records():
    """Sample audit records for testing."""
    return [
        {
            "run_id": "test_run_123",
            "timestamp": "2026-01-04T20:00:00",
            "tool_version": "0.1.0",
            "git_sha": "abc123",
            "python_version": "3.11.5",
            "input_file": "test.wav",
            "sample_rate": 16000,
            "slice_index": 0,
            "slice_start_s": 0.0,
            "slice_duration_s": 10.0,
            "perturbation_name": "none",
            "perturbation_params": {"seed": 1337},
            "indicators": {
                "spectral_centroid_mean": 1500.0,
                "rms_energy": 0.05,
            },
            "deferral": {
                "recommended_action": "accept",
                "fragility_score": 0.1,
                "reasons": [],
            },
            "warnings": [],
        },
        {
            "run_id": "test_run_123",
            "timestamp": "2026-01-04T20:00:01",
            "tool_version": "0.1.0",
            "git_sha": "abc123",
            "python_version": "3.11.5",
            "input_file": "test.wav",
            "sample_rate": 16000,
            "slice_index": 0,
            "slice_start_s": 0.0,
            "slice_duration_s": 10.0,
            "perturbation_name": "noise",
            "perturbation_params": {"snr_db": 20.0, "seed": 1337},
            "indicators": {
                "spectral_centroid_mean": 1520.0,
                "rms_energy": 0.06,
            },
            "deferral": {
                "recommended_action": "accept",
                "fragility_score": 0.1,
                "reasons": [],
            },
            "warnings": [],
        },
        {
            "run_id": "test_run_123",
            "timestamp": "2026-01-04T20:00:02",
            "tool_version": "0.1.0",
            "git_sha": "abc123",
            "python_version": "3.11.5",
            "input_file": "test.wav",
            "sample_rate": 16000,
            "slice_index": 1,
            "slice_start_s": 10.0,
            "slice_duration_s": 10.0,
            "perturbation_name": "none",
            "perturbation_params": {"seed": 1337},
            "indicators": {
                "spectral_centroid_mean": 2000.0,
                "rms_energy": 0.08,
            },
            "deferral": {
                "recommended_action": "defer_to_review",
                "fragility_score": 0.4,
                "reasons": ["high_fragility"],
            },
            "warnings": [],
        },
        {
            "run_id": "test_run_123",
            "timestamp": "2026-01-04T20:00:03",
            "tool_version": "0.1.0",
            "git_sha": "abc123",
            "python_version": "3.11.5",
            "input_file": "test.wav",
            "sample_rate": 16000,
            "slice_index": 1,
            "slice_start_s": 10.0,
            "slice_duration_s": 10.0,
            "perturbation_name": "noise",
            "perturbation_params": {"snr_db": 20.0, "seed": 1337},
            "indicators": {
                "spectral_centroid_mean": 2500.0,
                "rms_energy": 0.09,
            },
            "deferral": {
                "recommended_action": "defer_to_review",
                "fragility_score": 0.4,
                "reasons": ["high_fragility"],
            },
            "warnings": [],
        },
    ]


def test_load_audit_records(tmp_path, sample_audit_records):
    """Test loading audit records from JSONL file."""
    audit_file = tmp_path / "audit.jsonl"

    # Write sample records to file
    with open(audit_file, "w") as f:
        for record in sample_audit_records:
            f.write(json.dumps(record) + "\n")

    # Load records
    loaded = load_audit_records(audit_file)

    assert len(loaded) == len(sample_audit_records)
    assert loaded[0]["run_id"] == "test_run_123"
    assert loaded[0]["slice_index"] == 0


def test_load_audit_records_file_not_found(tmp_path):
    """Test that load_audit_records raises error for missing file."""
    audit_file = tmp_path / "nonexistent.jsonl"

    with pytest.raises(FileNotFoundError):
        load_audit_records(audit_file)


def test_load_audit_records_malformed_json(tmp_path):
    """Test that load_audit_records raises error for malformed JSON."""
    audit_file = tmp_path / "malformed.jsonl"

    with open(audit_file, "w") as f:
        f.write("not valid json\n")

    with pytest.raises(ValueError, match="Malformed JSON"):
        load_audit_records(audit_file)


def test_load_audit_records_empty_file(tmp_path):
    """Test that load_audit_records raises error for empty file."""
    audit_file = tmp_path / "empty.jsonl"

    # Create empty file
    audit_file.touch()

    with pytest.raises(ValueError, match="No records found"):
        load_audit_records(audit_file)


def test_compute_summary(sample_audit_records):
    """Test computing summary statistics."""
    summary = compute_summary(sample_audit_records)

    # Check metadata
    assert summary["run_id"] == "test_run_123"
    assert summary["total_records"] == 4
    assert summary["total_slices"] == 2
    assert set(summary["perturbations"]) == {"none", "noise"}

    # Check deferral summary
    assert summary["deferral_summary"]["counts"]["accept"] == 1
    assert summary["deferral_summary"]["counts"]["defer_to_review"] == 1
    assert summary["deferral_summary"]["percentages"]["accept"] == 50.0
    assert summary["deferral_summary"]["percentages"]["defer_to_review"] == 50.0

    # Check fragility summary
    assert "mean" in summary["fragility_summary"]
    assert "std" in summary["fragility_summary"]
    assert summary["fragility_summary"]["mean"] == 0.25  # (0.1 + 0.4) / 2

    # Check indicator statistics
    assert "spectral_centroid_mean" in summary["indicator_statistics"]
    assert "rms_energy" in summary["indicator_statistics"]

    # Check slice details
    assert len(summary["slice_details"]) == 2
    assert summary["slice_details"][0]["slice_index"] == 0
    assert summary["slice_details"][1]["slice_index"] == 1


def test_compute_summary_empty_records():
    """Test that compute_summary handles empty records list."""
    summary = compute_summary([])
    assert summary == {}


def test_write_summary(tmp_path, sample_audit_records):
    """Test writing summary to JSON file."""
    output_file = tmp_path / "summary.json"

    summary = compute_summary(sample_audit_records)
    write_summary(summary, output_file)

    assert output_file.exists()

    # Read and verify
    with open(output_file) as f:
        loaded_summary = json.load(f)

    assert loaded_summary["run_id"] == summary["run_id"]
    assert loaded_summary["total_slices"] == summary["total_slices"]


def test_write_summary_creates_parent_dirs(tmp_path, sample_audit_records):
    """Test that write_summary creates parent directories."""
    output_file = tmp_path / "subdir" / "nested" / "summary.json"

    summary = compute_summary(sample_audit_records)
    write_summary(summary, output_file)

    assert output_file.exists()


def test_generate_summary_report(tmp_path, sample_audit_records):
    """Test full summary report generation."""
    audit_file = tmp_path / "audit.jsonl"
    output_file = tmp_path / "summary.json"

    # Write sample records
    with open(audit_file, "w") as f:
        for record in sample_audit_records:
            f.write(json.dumps(record) + "\n")

    # Generate report
    summary = generate_summary_report(audit_file, output_file)

    # Verify summary
    assert summary["total_slices"] == 2
    assert summary["total_records"] == 4

    # Verify output file
    assert output_file.exists()

    with open(output_file) as f:
        loaded_summary = json.load(f)

    assert loaded_summary == summary


def test_generate_summary_report_file_not_found(tmp_path):
    """Test that generate_summary_report raises error for missing audit file."""
    audit_file = tmp_path / "nonexistent.jsonl"
    output_file = tmp_path / "summary.json"

    with pytest.raises(FileNotFoundError):
        generate_summary_report(audit_file, output_file)
