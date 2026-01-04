"""
Lightweight Python helper for Sonotheia voice fraud detection workflows.

Usage:
    SONOTHEIA_API_KEY=... python main.py path/to/audio.wav --enrollment-id enroll-123 --session-id session-123
"""

from __future__ import annotations

import argparse
import json
import sys

import requests

from client import SonotheiaClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Sonotheia voice fraud API examples")
    parser.add_argument("audio", help="Path to WAV/Opus audio to submit")
    parser.add_argument("--enrollment-id", help="Enrollment/voiceprint identifier for MFA verification")
    parser.add_argument("--session-id", help="Session identifier to link SARs and risk events")
    parser.add_argument("--decision", default="review", help="Decision for SAR submission (allow/deny/review)")
    parser.add_argument("--reason", default="Manual review requested", help="Human readable SAR reason")

    args = parser.parse_args()

    try:
        client = SonotheiaClient()
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    results = {}

    # Always run deepfake detection
    try:
        results["deepfake"] = client.detect_deepfake(
            args.audio,
            metadata={"session_id": args.session_id or "demo-session", "channel": "web"},
        )
    except requests.HTTPError as exc:
        error_detail = exc.response.text if hasattr(exc, "response") else str(exc)
        print(f"Deepfake detection failed: {error_detail}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Deepfake detection failed: {exc}", file=sys.stderr)
        sys.exit(1)

    # Run MFA verification if enrollment ID provided
    if args.enrollment_id:
        try:
            results["mfa"] = client.verify_mfa(
                args.audio,
                args.enrollment_id,
                context={"session_id": args.session_id or "demo-session", "channel": "ivr"},
            )
        except requests.HTTPError as exc:
            error_detail = exc.response.text if hasattr(exc, "response") else str(exc)
            print(f"MFA verification failed: {error_detail}", file=sys.stderr)
            sys.exit(1)
        except Exception as exc:
            print(f"MFA verification failed: {exc}", file=sys.stderr)
            sys.exit(1)

    # Submit SAR if session ID provided
    if args.session_id:
        try:
            results["sar"] = client.submit_sar(
                args.session_id,
                decision=args.decision,
                reason=args.reason,
                metadata={"source": "public-example"},
            )
        except requests.HTTPError as exc:
            error_detail = exc.response.text if hasattr(exc, "response") else str(exc)
            print(f"SAR submission failed: {error_detail}", file=sys.stderr)
            sys.exit(1)
        except Exception as exc:
            print(f"SAR submission failed: {exc}", file=sys.stderr)
            sys.exit(1)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
