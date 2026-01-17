"""
CLI for audio trust harness.
"""

import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

import typer

from audio_trust_harness.audio import load_audio, slice_audio
from audio_trust_harness.audit import create_audit_record, write_audit_record
from audio_trust_harness.audit.viz import create_dashboard
from audio_trust_harness.batch import process_slices_parallel, process_slices_serial
from audio_trust_harness.calibrate import ConsistencyChecker
from audio_trust_harness.config import VALID_FFT_WINDOWS, configure_stft

app = typer.Typer(help="Audio Trust Harness - Stress-test tool for audio indicators")


@app.command()
def run(
    audio: Path = typer.Option(
        None, help="Path to input WAV file (required unless --demo is set)"
    ),
    out: Path = typer.Option(..., help="Path to output JSONL audit file"),
    demo: bool = typer.Option(False, help="Run in demo mode with synthetic audio"),
    slice_seconds: float = typer.Option(10.0, help="Duration of each slice in seconds"),
    hop_seconds: float = typer.Option(
        10.0, help="Hop duration between slices in seconds"
    ),
    seed: int = typer.Option(1337, help="Random seed for deterministic perturbations"),
    perturbations: str = typer.Option(
        "none,noise", help="Comma-separated list of perturbations"
    ),
    max_slices: int = typer.Option(None, help="Maximum number of slices to process"),
    parallel: bool = typer.Option(False, help="Enable parallel processing of slices"),
    workers: int = typer.Option(
        None, help="Number of worker processes (default: CPU count)"
    ),
    fragility_threshold: float = typer.Option(
        0.3, help="Fragility threshold (CV > threshold triggers deferral)"
    ),
    clipping_threshold: float = typer.Option(
        0.95, help="Clipping threshold (amplitude > threshold indicates clipping)"
    ),
    min_duration: float = typer.Option(
        0.5, help="Minimum slice duration in seconds for valid analysis"
    ),
    fft_window: str = typer.Option(
        "hann",
        help=f"FFT window function for spectral analysis. Options: {', '.join(VALID_FFT_WINDOWS)}",
    ),
    resample_backend: str = typer.Option(
        "scipy",
        help="Resampling backend: 'scipy' (default) or 'librosa' (higher quality, requires librosa)",
    ),
    summary_out: Path = typer.Option(
        None, help="Optional path to write summary JSON after run"
    ),
    dashboard_out: Path = typer.Option(
        None, help="Optional path to write HTML dashboard after run"
    ),
    open_dashboard: bool = typer.Option(
        False, help="Open the dashboard after generation (requires --dashboard-out)"
    ),
):
    """
    Run the audio trust harness on an audio file.

    Processes audio slices, applies perturbations, computes indicators,
    and outputs audit records to JSONL.
    """
    # Configure FFT window type
    try:
        configure_stft(window=fft_window)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    # Parse perturbations list
    perturbation_names = [p.strip() for p in perturbations.split(",") if p.strip()]
    if not perturbation_names:
        typer.echo(
            "No valid perturbations provided. Use comma-separated names like 'none,noise'.",
            err=True,
        )
        raise typer.Exit(1)

    # Generate run ID
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    # Handle Demo Mode
    if demo:
        if audio:
            typer.echo("Error: --audio and --demo cannot be used together.", err=True)
            raise typer.Exit(1)

        # Run generation script
        import subprocess

        typer.echo("Generating demo assets...")
        script_path = (
            Path(__file__).parent.parent.parent / "scripts" / "generate_demo_audio.py"
        )
        try:
            subprocess.run([sys.executable, str(script_path)], check=True)
        except subprocess.CalledProcessError:
            typer.echo("Error: Failed to generate demo audio.", err=True)
            raise typer.Exit(1)

        # Use path relative to module location, not working directory
        project_root = Path(__file__).parent.parent.parent
        audio = project_root / "examples" / "test-audio" / "clean_tone.wav"
        typer.echo(f"Demo mode: Using generated file {audio}")

    if not audio:
        typer.echo("Error: Missing argument 'AUDIO'.", err=True)
        raise typer.Exit(1)
    if not demo and not audio.exists():
        typer.echo(f"Error: Audio file not found: {audio}", err=True)
        raise typer.Exit(1)

    out.parent.mkdir(parents=True, exist_ok=True)
    if summary_out:
        summary_out.parent.mkdir(parents=True, exist_ok=True)
    if dashboard_out:
        dashboard_out.parent.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Starting run: {run_id}")
    typer.echo(f"Input file: {audio}")
    typer.echo(f"Output file: {out}")

    # Load audio
    typer.echo(f"Loading audio (target: 16kHz mono, resampler: {resample_backend})...")
    try:
        audio_data, sample_rate = load_audio(
            audio, target_sr=16000, resample_backend=resample_backend
        )
    except Exception as e:
        typer.echo(f"Error loading audio: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Loaded: {len(audio_data)} samples at {sample_rate} Hz")
    typer.echo(f"Duration: {len(audio_data) / sample_rate:.2f}s")

    # Slice audio
    typer.echo(
        f"Slicing audio (slice={slice_seconds}s, hop={hop_seconds}s, max={max_slices})..."
    )
    try:
        slices = slice_audio(
            audio_data,
            sample_rate,
            slice_seconds=slice_seconds,
            hop_seconds=hop_seconds,
            max_slices=max_slices,
        )
    except ValueError as e:
        typer.echo(f"Invalid slicing parameters: {e}", err=True)
        raise typer.Exit(1)
    typer.echo(f"Created {len(slices)} slices")

    # Clear output file if it exists
    if out.exists():
        out.unlink()

    # Process slices (serial or parallel)
    if parallel:
        typer.echo(f"Processing slices in parallel (workers={workers or 'auto'})...")
        results = process_slices_parallel(
            slices,
            perturbation_names,
            seed,
            workers,
            fragility_threshold,
            clipping_threshold,
            min_duration,
        )
    else:
        typer.echo("Processing slices serially...")
        results = process_slices_serial(
            slices,
            perturbation_names,
            seed,
            fragility_threshold,
            clipping_threshold,
            min_duration,
        )

    # Write audit records and collect indicators for consistency check
    total_records = 0
    slice_indicators_for_consistency = []

    for result in results:
        # Collect indicators from 'none' perturbation for consistency check
        if "none" in result["indicators_by_perturbation"]:
            slice_indicators_for_consistency.append(
                result["indicators_by_perturbation"]["none"].copy()
            )

        # Write audit records for each perturbation
        for perturbation_name in perturbation_names:
            perturbation = result["perturbation_objects"].get(perturbation_name)
            if (
                perturbation is None
                or perturbation_name not in result["indicators_by_perturbation"]
            ):
                continue

            record = create_audit_record(
                run_id=run_id,
                input_file=str(audio),
                sample_rate=result["sample_rate"],
                slice_index=result["slice_index"],
                slice_start_s=result["slice_start_s"],
                slice_duration_s=result["slice_duration_s"],
                perturbation_name=perturbation_name,
                perturbation_params=perturbation.get_params(),
                indicators=result["indicators_by_perturbation"][perturbation_name],
                deferral_action=result["deferral_action"],
                fragility_score=result["fragility_score"],
                reasons=result["reasons"],
            )

            write_audit_record(record, out)
            total_records += 1

    # Perform cross-slice consistency check
    typer.echo("\nChecking cross-slice temporal consistency...")
    consistency_checker = ConsistencyChecker()
    consistency_result = consistency_checker.evaluate(slice_indicators_for_consistency)

    if consistency_result.is_consistent:
        typer.echo("  ✓ Temporal consistency: PASS")
    else:
        typer.echo("  ⚠ Temporal consistency: FAIL")
        typer.echo(
            f"    Inconsistency score: {consistency_result.inconsistency_score:.3f}"
        )
        typer.echo(
            f"    Inconsistent indicators: {', '.join(consistency_result.inconsistent_indicators)}"
        )

    typer.echo(f"\n✓ Complete! Wrote {total_records} records to {out}")
    typer.echo(
        f"  Processed {len(slices)} slices with {len(perturbation_names)} perturbations"
    )

    # Summary statistics
    actions = {"accept": 0, "defer_to_review": 0, "insufficient_evidence": 0}

    # Quick count (re-read file to count actions per slice, not per perturbation)
    slice_actions: dict[int, str | None] = {}
    for slice_obj in slices:
        # Use the deferral from the last written record for this slice
        # (all perturbations for same slice have same deferral decision)
        slice_actions[slice_obj.slice_index] = None

    if total_records == 0:
        typer.echo(
            "\nNo slices were processed (audio may be too short for the given slice/hop duration)."
        )
        return

    # Read records and collect unique slice decisions
    with open(out) as f:
        for line in f:
            record_data = json.loads(line)
            idx = record_data["slice_index"]
            action = record_data["deferral"]["recommended_action"]
            slice_actions[idx] = action

    for action in slice_actions.values():
        if action in actions:
            actions[action] += 1

    typer.echo("\nDeferral summary:")
    typer.echo(f"  accept: {actions['accept']}")
    typer.echo(f"  defer_to_review: {actions['defer_to_review']}")
    typer.echo(f"  insufficient_evidence: {actions['insufficient_evidence']}")

    if summary_out:
        from audio_trust_harness.audit.summary import generate_summary_report

        typer.echo("\nGenerating summary report...")
        try:
            generate_summary_report(out, summary_out)
            typer.echo(f"  ✓ Summary written to {summary_out}")
        except Exception as e:
            typer.echo(f"  ⚠ Failed to write summary: {e}", err=True)

    if dashboard_out:
        typer.echo("\nGenerating dashboard...")
        try:
            create_dashboard(str(out), str(dashboard_out))
            typer.echo(f"  ✓ Dashboard written to {dashboard_out}")
        except Exception as e:
            typer.echo(f"  ⚠ Failed to generate dashboard: {e}", err=True)

    if open_dashboard:
        if not dashboard_out:
            typer.echo(
                "\n⚠ Cannot open dashboard without --dashboard-out. Skipping open.",
                err=True,
            )
        else:
            import webbrowser

            typer.echo("\nOpening dashboard in your browser...")
            webbrowser.open(Path(dashboard_out).resolve().as_uri())

    if not summary_out and not dashboard_out:
        typer.echo("\nNext steps:")
        typer.echo("  - Generate summary: audio_trust_harness summary --audit <audit.jsonl> --out summary.json")
        typer.echo("  - Generate dashboard: audio_trust_harness visualize --audit <audit.jsonl> --out dashboard.html")


@app.command()
def summary(
    audit: Path = typer.Option(..., help="Path to input JSONL audit file"),
    out: Path = typer.Option(..., help="Path to output JSON summary file"),
    print_summary: bool = typer.Option(False, help="Print summary to stdout"),
):
    """
    Generate summary report from audit log.

    Aggregates statistics across all slices and perturbations.
    """
    from audio_trust_harness.audit.summary import generate_summary_report

    typer.echo(f"Reading audit log: {audit}")

    try:
        summary_data = generate_summary_report(audit, out)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"\n✓ Summary report written to {out}")
    typer.echo("\nQuick Stats:")
    typer.echo(f"  Total slices: {summary_data['total_slices']}")
    typer.echo(f"  Total records: {summary_data['total_records']}")
    typer.echo(f"  Perturbations: {', '.join(summary_data['perturbations'])}")
    typer.echo("\nDeferral Summary:")
    for action, count in summary_data["deferral_summary"]["counts"].items():
        pct = summary_data["deferral_summary"]["percentages"][action]
        typer.echo(f"  {action}: {count} ({pct}%)")
    typer.echo(
        f"  Mean: {summary_data['fragility_summary']['mean']:.4f} "
        f"(±{summary_data['fragility_summary']['std']:.4f})"
    )

    if print_summary:
        import sys

        json.dump(summary_data, sys.stdout, indent=2)
        print()  # Newline


@app.command()
def visualize(
    audit: Path = typer.Option(..., help="Path to input JSONL audit file"),
    out: Path = typer.Option(None, help="Path to output HTML dashboard file"),
):
    """
    Generate and open a visualization dashboard from audit log.
    """
    typer.echo(f"Generating dashboard for: {audit}")
    try:
        if out:
            create_dashboard(str(audit), str(out))
        else:
            create_dashboard(str(audit), None)
    except Exception as e:
        typer.echo(f"Error generating dashboard: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def showcase(
    fixture: str = typer.Option(
        ...,
        help=(
            "Name of synthetic fixture: clean_speech, noisy_speech, tone, noise, "
            "turntaking_normal, turntaking_anomalous, overlap_high"
        ),
    ),
    out: Path = typer.Option(..., help="Path to output JSONL audit file"),
):
    """
    Run showcase evaluation with deterministic, public-safe sensors.

    Demonstrates Sonotheia's evidence-first voice risk assessment using
    synthetic fixtures. Emits audit JSONL records with signals, confidence,
    reason_codes, and recommended_action.

    Fixtures:
    - clean_speech: Multi-harmonic speech-like signal
    - noisy_speech: Speech with ambient noise
    - tone: Simple 440Hz tone
    - noise: White noise
    - turntaking_normal: Normal turn-taking pattern (alternating speech/pauses)
    - turntaking_anomalous: Anomalous turn-taking (overlapping, no pauses)
    - overlap_high: High overlap (multiple simultaneous speakers)
    """
    from audio_trust_harness.runners import ShowcaseRunner

    valid_fixtures = {
        "clean_speech",
        "noisy_speech",
        "tone",
        "noise",
        "turntaking_normal",
        "turntaking_anomalous",
        "overlap_high",
    }

    if fixture not in valid_fixtures:
        typer.echo(
            f"Error: Invalid fixture '{fixture}'. "
            f"Valid options: {', '.join(sorted(valid_fixtures))}",
            err=True,
        )
        raise typer.Exit(1)

    typer.echo(f"Running showcase evaluation with fixture: {fixture}")
    typer.echo(f"Output file: {out}")

    # Clear output file if it exists
    if out.exists():
        out.unlink()

    try:
        runner = ShowcaseRunner()
        runner.run(fixture_name=fixture, output_path=out, deterministic=True)
        typer.echo(f"\n✓ Complete! Wrote audit record to {out}")
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    from audio_trust_harness import __version__
    from audio_trust_harness.audit import get_git_sha

    typer.echo(f"Audio Trust Harness v{__version__}")
    typer.echo(f"Git SHA: {get_git_sha()}")


def main():
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
