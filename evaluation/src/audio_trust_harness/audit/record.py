"""
Audit record schema and serialization.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from audio_trust_harness.utils.json_safety import convert_numpy_types


class DeferralInfo(BaseModel):
    """Deferral decision information."""

    recommended_action: str
    fragility_score: float
    reasons: list[str]


class AuditRecord(BaseModel):
    """
    Audit record for a processed audio slice with perturbation.

    All records are serializable to JSONL format.
    """

    run_id: str
    timestamp: str
    tool_version: str
    git_sha: str = Field(default="unknown")
    python_version: str
    input_file: str  # Basename only, never full path
    sample_rate: int
    slice_index: int
    slice_start_s: float
    slice_duration_s: float
    perturbation_name: str
    perturbation_params: dict[str, Any]
    indicators: dict[str, float]
    deferral: DeferralInfo
    warnings: list[str] = Field(default_factory=list)


def get_tool_version() -> str:
    """Get tool version from package."""
    try:
        from audio_trust_harness import __version__

        return __version__
    except ImportError:
        return "0.1.0"


def get_git_sha() -> str:
    """Get current git SHA if available."""
    try:
        # Try to find git repository root by traversing up from package directory
        repo_path = Path(__file__).parent
        for _ in range(5):  # Max 5 levels up
            if (repo_path / ".git").exists():
                break
            repo_path = repo_path.parent

        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,  # Don't raise on non-zero exit
            cwd=repo_path,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        # Git not available or timeout
        pass
    return "unknown"


def write_audit_record(record: AuditRecord, output_path: Path) -> None:
    """
    Write audit record to JSONL file.

    Args:
        record: AuditRecord to write
        output_path: Path to JSONL file (will append)
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to JSON line
    # record.model_dump_json() + "\n"

    # Append to file
    with open(output_path, "a") as f:
        # Pydantic's model_dump_json handles standard types but might struggle with nested numpy types
        # in dictionary fields if they weren't caught earlier.
        # Safer to dump to dict, clean, then serialize.
        clean_dict = convert_numpy_types(record.model_dump())
        import json

        f.write(json.dumps(clean_dict) + "\n")


def create_audit_record(
    run_id: str,
    input_file: str,
    sample_rate: int,
    slice_index: int,
    slice_start_s: float,
    slice_duration_s: float,
    perturbation_name: str,
    perturbation_params: dict[str, Any],
    indicators: dict[str, float],
    deferral_action: str,
    fragility_score: float,
    reasons: list[str],
    warnings: list[str] | None = None,
) -> AuditRecord:
    """
    Create an audit record with current timestamp and version info.

    Args:
        run_id: Unique run identifier
        input_file: Input filename (basename only)
        sample_rate: Sample rate in Hz
        slice_index: Index of the slice
        slice_start_s: Start time of slice in seconds
        slice_duration_s: Duration of slice in seconds
        perturbation_name: Name of applied perturbation
        perturbation_params: Parameters of the perturbation
        indicators: Computed indicator values
        deferral_action: Recommended action
        fragility_score: Fragility score
        reasons: Reason tags for the decision
        warnings: Optional list of warnings

    Returns:
        AuditRecord instance
    """
    # Get basename only (privacy/redaction)
    basename = Path(input_file).name

    return AuditRecord(
        run_id=run_id,
        timestamp=datetime.now().isoformat(),
        tool_version=get_tool_version(),
        git_sha=get_git_sha(),
        python_version=sys.version.split()[0],
        input_file=basename,
        sample_rate=sample_rate,
        slice_index=slice_index,
        slice_start_s=slice_start_s,
        slice_duration_s=slice_duration_s,
        perturbation_name=perturbation_name,
        perturbation_params=perturbation_params,
        indicators=indicators,
        deferral=DeferralInfo(
            recommended_action=deferral_action,
            fragility_score=fragility_score,
            reasons=reasons,
        ),
        warnings=warnings or [],
    )
