"""
Summary report generation from audit logs.
"""

import json
from pathlib import Path
from typing import Any

import numpy as np


def load_audit_records(audit_file: Path) -> list[dict[str, Any]]:
    """
    Load audit records from JSONL file.

    Args:
        audit_file: Path to JSONL audit file

    Returns:
        List of audit record dictionaries

    Raises:
        FileNotFoundError: If audit file doesn't exist
        ValueError: If audit file is malformed
    """
    if not audit_file.exists():
        raise FileNotFoundError(f"Audit file not found: {audit_file}")

    records = []
    with open(audit_file) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                records.append(record)
            except json.JSONDecodeError as e:
                raise ValueError(f"Malformed JSON on line {line_num}: {e}")

    if not records:
        raise ValueError(f"No records found in {audit_file}")

    return records


def compute_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute summary statistics from audit records.

    Args:
        records: List of audit record dictionaries

    Returns:
        Summary dictionary with aggregated statistics
    """
    if not records:
        return {}

    # Group records by slice and perturbation
    slices = {}
    perturbations_set = set()

    for record in records:
        slice_idx = record["slice_index"]
        perturbation = record["perturbation_name"]
        perturbations_set.add(perturbation)

        if slice_idx not in slices:
            # Store deferral from first record for this slice
            # Note: All perturbations for same slice should have identical deferral decisions
            # as they are computed once per slice across all perturbations (see cli.py)
            slices[slice_idx] = {
                "slice_index": slice_idx,
                "slice_start_s": record["slice_start_s"],
                "slice_duration_s": record["slice_duration_s"],
                "perturbations": {},
                "deferral_action": record["deferral"]["recommended_action"],
                "fragility_score": record["deferral"]["fragility_score"],
            }

        slices[slice_idx]["perturbations"][perturbation] = {
            "indicators": record["indicators"],
            "perturbation_params": record["perturbation_params"],
        }

    # Collect all indicator names
    indicator_names = set()
    for record in records:
        indicator_names.update(record["indicators"].keys())

    # Compute aggregated statistics
    deferral_counts = {"accept": 0, "defer_to_review": 0, "insufficient_evidence": 0}
    fragility_scores = []

    for slice_data in slices.values():
        action = slice_data["deferral_action"]
        if action in deferral_counts:
            deferral_counts[action] += 1
        fragility_scores.append(slice_data["fragility_score"])

    # Compute indicator statistics across all records
    indicator_stats = {}
    for indicator_name in indicator_names:
        values = [
            record["indicators"][indicator_name]
            for record in records
            if indicator_name in record["indicators"]
        ]
        if values:
            indicator_stats[indicator_name] = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "median": float(np.median(values)),
            }

    # Extract metadata from first record
    first_record = records[0]

    summary = {
        "run_id": first_record["run_id"],
        "tool_version": first_record["tool_version"],
        "git_sha": first_record["git_sha"],
        "input_file": first_record["input_file"],
        "sample_rate": first_record["sample_rate"],
        "total_records": len(records),
        "total_slices": len(slices),
        "perturbations": sorted(list(perturbations_set)),
        "deferral_summary": {
            "counts": deferral_counts,
            "percentages": {
                action: round(100 * count / len(slices), 2) if len(slices) > 0 else 0.0
                for action, count in deferral_counts.items()
            },
        },
        "fragility_summary": {
            "mean": float(np.mean(fragility_scores)) if fragility_scores else 0.0,
            "std": float(np.std(fragility_scores)) if fragility_scores else 0.0,
            "min": float(np.min(fragility_scores)) if fragility_scores else 0.0,
            "max": float(np.max(fragility_scores)) if fragility_scores else 0.0,
            "median": float(np.median(fragility_scores)) if fragility_scores else 0.0,
        },
        "indicator_statistics": indicator_stats,
        "slice_details": [
            {
                "slice_index": slice_data["slice_index"],
                "slice_start_s": slice_data["slice_start_s"],
                "slice_duration_s": slice_data["slice_duration_s"],
                "deferral_action": slice_data["deferral_action"],
                "fragility_score": slice_data["fragility_score"],
                "perturbations": list(slice_data["perturbations"].keys()),
            }
            for slice_data in sorted(slices.values(), key=lambda x: x["slice_index"])
        ],
    }

    return summary


def write_summary(summary: dict[str, Any], output_path: Path) -> None:
    """
    Write summary to JSON file.

    Args:
        summary: Summary dictionary
        output_path: Path to output JSON file
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)


def generate_summary_report(audit_file: Path, output_file: Path) -> dict[str, Any]:
    """
    Generate summary report from audit JSONL file.

    Args:
        audit_file: Path to input JSONL audit file
        output_file: Path to output JSON summary file

    Returns:
        Summary dictionary

    Raises:
        FileNotFoundError: If audit file doesn't exist
        ValueError: If audit file is malformed or empty
    """
    records = load_audit_records(audit_file)
    summary = compute_summary(records)
    write_summary(summary, output_file)
    return summary
