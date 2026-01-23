r"""
Lightweight Python helper for Sonotheia voice fraud detection workflows.

Usage:
    SONOTHEIA_API_KEY=... python main.py path/to/audio.wav \\
        --enrollment-id enroll-123 --session-id session-123
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import requests

from client import SonotheiaClient
from constants import ALLOWED_AUDIO_EXTENSIONS


@contextmanager
def handle_api_errors(operation_name: str) -> Iterator[None]:
    """Context manager to handle API errors consistently.

    Args:
        operation_name: Name of the operation for error messages

    Raises:
        SystemExit: On any error with appropriate exit code
    """
    try:
        yield
    except requests.HTTPError as exc:
        error_detail = exc.response.text if hasattr(exc, "response") else str(exc)
        print(f"{operation_name} failed: {error_detail}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"{operation_name} failed: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sonotheia voice fraud API examples")
    parser.add_argument("audio", help="Path to WAV/Opus audio to submit")
    parser.add_argument(
        "--enrollment-id", help="Enrollment/voiceprint identifier for MFA verification"
    )
    parser.add_argument("--session-id", help="Session identifier to link SARs and risk events")
    parser.add_argument(
        "--decision",
        default="review",
        choices=("allow", "deny", "review"),
        help="Decision for SAR submission (allow/deny/review)",
    )
    parser.add_argument(
        "--reason", default="Manual review requested", help="Human readable SAR reason"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write JSON results",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output (useful for terminal viewing)",
    )

    args = parser.parse_args()

    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"Audio file not found: {audio_path}", file=sys.stderr)
        sys.exit(1)

    if audio_path.suffix.lower() not in ALLOWED_AUDIO_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_AUDIO_EXTENSIONS))
        print(
            f"Unsupported audio extension '{audio_path.suffix}'. " f"Supported formats: {allowed}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        client = SonotheiaClient()
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    results: dict[str, object] = {}
    session_id = args.session_id or "demo-session"

    # Always run deepfake detection
    with handle_api_errors("Deepfake detection"):
        results["deepfake"] = client.detect_deepfake(
            args.audio,
            metadata={"session_id": session_id, "channel": "web"},
        )

    # Run MFA verification if enrollment ID provided
    if args.enrollment_id:
        with handle_api_errors("MFA verification"):
            results["mfa"] = client.verify_mfa(
                args.audio,
                args.enrollment_id,
                context={"session_id": session_id, "channel": "ivr"},
            )

    # Submit SAR if session ID provided
    if args.session_id:
        with handle_api_errors("SAR submission"):
            results["sar"] = client.submit_sar(
                args.session_id,
                decision=args.decision,
                reason=args.reason,
                metadata={"source": "public-example"},
            )

    indent = 2 if args.pretty else None
    payload = json.dumps(results, indent=indent)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
        print(f"Wrote results to {args.output}")
    else:
        print(payload)


if __name__ == "__main__":
    main()
