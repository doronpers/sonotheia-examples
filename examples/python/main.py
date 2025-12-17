"""
Lightweight Python helper for Sonotheia voice fraud detection workflows.

Usage:
    SONOTHEIA_API_KEY=... python main.py path/to/audio.wav --enrollment-id enroll-123 --session-id session-123
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

import requests


API_URL = os.getenv("SONOTHEIA_API_URL", "https://api.sonotheia.com").rstrip("/")
API_KEY = os.getenv("SONOTHEIA_API_KEY")
DEEPFAKE_PATH = os.getenv("SONOTHEIA_DEEPFAKE_PATH", "/v1/voice/deepfake")
MFA_PATH = os.getenv("SONOTHEIA_MFA_PATH", "/v1/mfa/voice/verify")
SAR_PATH = os.getenv("SONOTHEIA_SAR_PATH", "/v1/reports/sar")


def _require_api_key() -> str:
    if not API_KEY:
        print("Set SONOTHEIA_API_KEY before running examples.", file=sys.stderr)
        sys.exit(1)
    return API_KEY


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_require_api_key()}",
        "Accept": "application/json",
    }


def detect_deepfake(audio_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{API_URL}{DEEPFAKE_PATH}"
    with open(audio_path, "rb") as audio_file:
        files = {"audio": (os.path.basename(audio_path), audio_file, "audio/wav")}
        data = {"metadata": json.dumps(metadata or {})}
        response = requests.post(url, headers=_headers(), files=files, data=data, timeout=30)
    response.raise_for_status()
    return response.json()


def verify_mfa(
    audio_path: str,
    enrollment_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    url = f"{API_URL}{MFA_PATH}"
    with open(audio_path, "rb") as audio_file:
        files = {"audio": (os.path.basename(audio_path), audio_file, "audio/wav")}
        data = {
            "enrollment_id": enrollment_id,
            "context": json.dumps(context or {}),
        }
        response = requests.post(url, headers=_headers(), files=files, data=data, timeout=30)
    response.raise_for_status()
    return response.json()


def submit_sar(
    session_id: str,
    decision: str,
    reason: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    url = f"{API_URL}{SAR_PATH}"
    payload = {
        "session_id": session_id,
        "decision": decision,
        "reason": reason,
        "metadata": metadata or {},
    }
    response = requests.post(url, headers=_headers(), json=payload, timeout=15)
    response.raise_for_status()
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Sonotheia voice fraud API examples")
    parser.add_argument("audio", help="Path to WAV/Opus audio to submit")
    parser.add_argument("--enrollment-id", help="Enrollment/voiceprint identifier for MFA verification")
    parser.add_argument("--session-id", help="Session identifier to link SARs and risk events")
    parser.add_argument("--decision", default="review", help="Decision for SAR submission (allow/deny/review)")
    parser.add_argument("--reason", default="Manual review requested", help="Human readable SAR reason")

    args = parser.parse_args()
    _require_api_key()

    results: Dict[str, Any] = {}

    try:
        results["deepfake"] = detect_deepfake(
            args.audio,
            metadata={"session_id": args.session_id or "demo-session", "channel": "web"},
        )
    except requests.HTTPError as exc:
        print(f"Deepfake detection failed: {exc.response.text}", file=sys.stderr)
        sys.exit(1)

    if args.enrollment_id:
        try:
            results["mfa"] = verify_mfa(
                args.audio,
                args.enrollment_id,
                context={"session_id": args.session_id or "demo-session", "channel": "ivr"},
            )
        except requests.HTTPError as exc:
            print(f"MFA verification failed: {exc.response.text}", file=sys.stderr)
            sys.exit(1)

    if args.session_id:
        try:
            results["sar"] = submit_sar(
                args.session_id,
                decision=args.decision,
                reason=args.reason,
                metadata={"source": "public-example"},
            )
        except requests.HTTPError as exc:
            print(f"SAR submission failed: {exc.response.text}", file=sys.stderr)
            sys.exit(1)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
