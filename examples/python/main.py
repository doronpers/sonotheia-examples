"""
Lightweight Python helper for Sonotheia voice fraud detection workflows.

Usage:
    SONOTHEIA_API_KEY=... python main.py path/to/audio.wav --enrollment-id enroll-123 --session-id session-123
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterator
from contextlib import contextmanager

import requests

from client import SonotheiaClient


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
    parser.add_argument(
        "--session-id", help="Session identifier to link SARs and risk events"
    )
    parser.add_argument(
        "--decision",
        default="review",
        help="Decision for SAR submission (allow/deny/review)",
    )
    parser.add_argument(
        "--reason", default="Manual review requested", help="Human readable SAR reason"
    )

    args = parser.parse_args()

    try:
        client = SonotheiaClient()
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    results = {}
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

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
