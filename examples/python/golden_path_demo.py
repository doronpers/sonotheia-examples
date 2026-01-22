"""
Golden Path Demo - Complete Sonotheia Workflow

Demonstrates the complete end-to-end workflow:
1. Deepfake detection
2. Voice MFA verification (optional)
3. Routing decision based on results
4. Optional SAR submission

Usage:
    # Mock mode (no API key required)
    python golden_path_demo.py audio.wav --mock

    # Real API mode
    export SONOTHEIA_API_KEY=your_key
    python golden_path_demo.py audio.wav

    # With MFA verification
    python golden_path_demo.py audio.wav --enrollment-id enroll-123

    # With SAR submission
    python golden_path_demo.py audio.wav --session-id session-123 --sar auto
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from client import SonotheiaClient
from utils import convert_numpy_types

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_audio_info(audio_path: Path) -> dict[str, Any]:
    """
    Get audio file information (duration, sample rate).

    Args:
        audio_path: Path to audio file

    Returns:
        Dict with audio_seconds and samplerate_hz
    """
    # Try soundfile first (faster, more reliable)
    try:
        import soundfile as sf

        info = sf.info(str(audio_path))
        return {
            "audio_seconds": float(info.duration),
            "samplerate_hz": int(info.samplerate),
        }
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"soundfile failed: {e}, trying ffprobe")

    # Fallback to ffprobe
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-show_entries",
                "stream=sample_rate",
                "-of",
                "json",
                str(audio_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        duration = float(data.get("format", {}).get("duration", 0))
        sample_rate = int(
            data.get("streams", [{}])[0].get("sample_rate", 16000) if data.get("streams") else 16000
        )
        return {
            "audio_seconds": duration,
            "samplerate_hz": sample_rate,
        }
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not get audio info: {e}, using defaults")
        return {
            "audio_seconds": 0.0,
            "samplerate_hz": 16000,
        }


def make_routing_decision(
    deepfake_result: dict[str, Any],
    mfa_result: dict[str, Any] | None = None,
    sar_policy: str = "auto",
) -> dict[str, Any]:
    """
    Make routing decision based on deepfake and MFA results.

    Args:
        deepfake_result: Deepfake detection result
        mfa_result: MFA verification result (optional)
        sar_policy: SAR submission policy (auto, never, always)

    Returns:
        Decision dict with route, reasons, and explainability
    """
    reasons: list[str] = []
    route = "ALLOW"
    human_summary_parts: list[str] = []

    # Check deepfake results
    deepfake_score = deepfake_result.get("score", 0.5)
    recommended_action = deepfake_result.get("recommended_action", "")

    # High deepfake score or defer recommendation
    if recommended_action == "defer_to_review" or deepfake_score > 0.7:
        route = "ESCALATE_TO_HUMAN"
        reasons.append("deepfake_defer")
        human_summary_parts.append(
            f"Deepfake score {deepfake_score:.2f} indicates potential synthetic audio"
        )
    elif deepfake_score > 0.5:
        route = "REQUIRE_STEP_UP"
        reasons.append("elevated_risk")
        human_summary_parts.append(f"Elevated risk detected (score: {deepfake_score:.2f})")

    # Check MFA results
    if mfa_result:
        verified = mfa_result.get("verified", False)
        confidence = mfa_result.get("confidence", 0.0)

        if not verified:
            if route == "ALLOW":
                route = "REQUIRE_STEP_UP"
            elif route == "REQUIRE_STEP_UP":
                route = "REQUIRE_CALLBACK"
            else:
                route = "ESCALATE_TO_HUMAN"
            reasons.append("mfa_verification_failed")
            human_summary_parts.append("Voice MFA verification failed")
        elif confidence < 0.7:
            if route == "ALLOW":
                route = "REQUIRE_STEP_UP"
            reasons.append("low_mfa_confidence")
            human_summary_parts.append(f"Low MFA confidence ({confidence:.2f})")

    # Determine SAR submission
    should_submit_sar = False
    if sar_policy == "always":
        should_submit_sar = True
    elif sar_policy == "never":
        should_submit_sar = False
    elif sar_policy == "auto":
        # Submit SAR if escalating or blocking
        should_submit_sar = route in ("ESCALATE_TO_HUMAN", "BLOCK") or deepfake_score > 0.8

    if should_submit_sar:
        reasons.append("sar_required")

    # Build human summary
    if not human_summary_parts:
        human_summary = "Low risk detected; standard processing allowed."
    else:
        human_summary = " ".join(human_summary_parts) + "."

    return {
        "route": route,
        "reasons": reasons,
        "explainability": {
            "human_summary": human_summary,
        },
        "should_submit_sar": should_submit_sar,
    }


def run_golden_path(
    audio_path: Path,
    enrollment_id: str | None = None,
    session_id: str | None = None,
    sar_policy: str = "auto",
    mock_mode: bool = False,
    api_url: str | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Run the complete golden path workflow.

    Args:
        audio_path: Path to audio file
        enrollment_id: Optional enrollment ID for MFA
        session_id: Optional session ID (auto-generated if not provided)
        sar_policy: SAR submission policy (auto, never, always)
        mock_mode: Use mock API server
        api_url: Override API URL
        verbose: Enable verbose logging

    Returns:
        Complete workflow result in standardized format
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Generate session ID if not provided
    if not session_id:
        session_id = f"session-{uuid.uuid4().hex[:12]}"

    # Get audio info
    audio_info = get_audio_info(audio_path)
    logger.info(
        f"Audio file: {audio_path.name}, "
        f"duration: {audio_info['audio_seconds']:.2f}s, "
        f"sample rate: {audio_info['samplerate_hz']}Hz"
    )

    # Initialize client
    if mock_mode:
        # Use mock server URL
        mock_url = api_url or os.getenv("SONOTHEIA_API_URL", "http://localhost:8000")
        # Allow mock mode without API key
        api_key = os.getenv("SONOTHEIA_API_KEY", "mock_api_key_12345")
        client = SonotheiaClient(api_key=api_key, api_url=mock_url)
        logger.info(f"Using mock API server at {mock_url}")
    else:
        try:
            client = SonotheiaClient(api_url=api_url)
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise

    results: dict[str, Any] = {}
    diagnostics: dict[str, Any] = {"retries": 0}

    # Step 1: Deepfake detection
    logger.info("Running deepfake detection...")
    try:
        start_time = time.time()
        deepfake_result = client.detect_deepfake(
            str(audio_path), metadata={"session_id": session_id, "channel": "web"}
        )
        latency_ms = int((time.time() - start_time) * 1000)

        # Add latency if not present
        if "latency_ms" not in deepfake_result:
            deepfake_result["latency_ms"] = latency_ms

        # Add recommended_action if not present (for mock mode compatibility)
        if "recommended_action" not in deepfake_result:
            score = deepfake_result.get("score", 0.5)
            if score > 0.7:
                deepfake_result["recommended_action"] = "defer_to_review"
            elif score > 0.5:
                deepfake_result["recommended_action"] = "review"
            else:
                deepfake_result["recommended_action"] = "allow"

        results["deepfake"] = convert_numpy_types(deepfake_result)
        logger.info(
            f"Deepfake detection: score={deepfake_result.get('score', 0):.3f}, "
            f"label={deepfake_result.get('label', 'unknown')}"
        )
    except requests.HTTPError as e:
        logger.error(f"Deepfake detection failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Deepfake detection error: {e}")
        raise

    # Step 2: MFA verification (if enrollment ID provided)
    if enrollment_id:
        logger.info(f"Running MFA verification for enrollment: {enrollment_id}")
        try:
            start_time = time.time()
            mfa_result = client.verify_mfa(
                str(audio_path),
                enrollment_id,
                context={"session_id": session_id, "channel": "ivr"},
            )
            latency_ms = int((time.time() - start_time) * 1000)

            # Add latency if not present
            if "latency_ms" not in mfa_result:
                mfa_result["latency_ms"] = latency_ms

            results["mfa"] = convert_numpy_types(mfa_result)
            logger.info(
                f"MFA verification: verified={mfa_result.get('verified', False)}, "
                f"confidence={mfa_result.get('confidence', 0):.3f}"
            )
        except requests.HTTPError as e:
            logger.warning(f"MFA verification failed: {e}")
            # Continue without MFA result
            results["mfa"] = None
        except Exception as e:
            logger.warning(f"MFA verification error: {e}")
            results["mfa"] = None
    else:
        results["mfa"] = None

    # Step 3: Make routing decision
    logger.info("Making routing decision...")
    decision = make_routing_decision(
        results["deepfake"],
        results.get("mfa"),
        sar_policy=sar_policy,
    )
    logger.info(f"Routing decision: {decision['route']}")

    # Step 4: SAR submission (if policy allows)
    if decision.get("should_submit_sar", False) and session_id:
        logger.info("Submitting SAR...")
        try:
            sar_result = client.submit_sar(
                session_id,
                decision="review" if decision["route"] == "ESCALATE_TO_HUMAN" else "deny",
                reason=decision["explainability"]["human_summary"],
                metadata={"source": "golden_path_demo", "route": decision["route"]},
            )
            results["sar"] = convert_numpy_types(sar_result)
            logger.info(f"SAR submitted: case_id={sar_result.get('case_id', 'unknown')}")
        except requests.HTTPError as e:
            logger.warning(f"SAR submission failed: {e}")
            results["sar"] = None
        except Exception as e:
            logger.warning(f"SAR submission error: {e}")
            results["sar"] = None
    else:
        results["sar"] = None

    # Remove should_submit_sar from decision (internal only)
    decision.pop("should_submit_sar", None)

    # Build final output
    output = {
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "inputs": {
            "audio_filename": audio_path.name,
            **audio_info,
        },
        "results": results,
        "decision": decision,
        "diagnostics": diagnostics,
    }

    return convert_numpy_types(output)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Golden Path Demo - Complete Sonotheia Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Mock mode (no API key required)
  python golden_path_demo.py audio.wav --mock

  # Real API mode
  export SONOTHEIA_API_KEY=your_key
  python golden_path_demo.py audio.wav

  # With MFA verification
  python golden_path_demo.py audio.wav --enrollment-id enroll-123

  # With SAR submission
  python golden_path_demo.py audio.wav --session-id session-123 --sar auto
        """,
    )
    parser.add_argument("audio", type=Path, help="Path to audio file (WAV, Opus, MP3, FLAC)")
    parser.add_argument(
        "--enrollment-id",
        help=(
            "Enrollment ID for MFA verification (optional). "
            "For mock mode, any string works. For production, obtain from enrollment process."
        ),
    )
    parser.add_argument(
        "--session-id",
        help="Session identifier (auto-generated if not provided)",
    )
    parser.add_argument(
        "--sar",
        choices=("auto", "never", "always"),
        default="auto",
        help="SAR submission policy: auto (submit if high risk), never, always (default: auto)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock API server instead of real API (no API key required)",
    )
    parser.add_argument(
        "--api-url",
        help=(
            "Override API URL "
            "(default: https://api.sonotheia.com or http://localhost:8000 for mock)"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON output to file (default: stdout)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Validate audio file
    if not args.audio.exists():
        print(f"Error: Audio file not found: {args.audio}", file=sys.stderr)
        sys.exit(1)

    allowed_extensions = {".wav", ".opus", ".mp3", ".flac"}
    if args.audio.suffix.lower() not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        print(
            f"Error: Unsupported audio extension '{args.audio.suffix}'. "
            f"Supported formats: {allowed}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Run golden path
    try:
        result = run_golden_path(
            audio_path=args.audio,
            enrollment_id=args.enrollment_id,
            session_id=args.session_id,
            sar_policy=args.sar,
            mock_mode=args.mock,
            api_url=args.api_url,
            verbose=args.verbose,
        )
    except Exception as e:
        # Return error in JSON format
        error_output = {
            "error": {
                "message": str(e),
                "type": type(e).__name__,
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(error_output, indent=2 if args.pretty else None))
        else:
            print(json.dumps(error_output, indent=2 if args.pretty else None))
        sys.exit(1)

    # Output result
    indent = 2 if args.pretty else None
    output_json = json.dumps(result, indent=indent)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_json)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
