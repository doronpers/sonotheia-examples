"""
Account Recovery Flow Example

Demonstrates integration for account recovery and password reset flows using
voice verification to prevent account takeover attacks.

Use Cases:
- Password reset verification
- Account recovery with voice MFA
- Security question bypass with voice verification
- Account unlock after suspicious activity

Example Usage:
    # Password reset with voice verification
    python account_recovery_flow.py audio.wav \
      --user-id user123 \
      --enrollment-id enroll-456 \
      --recovery-type password_reset

    # Account recovery
    python account_recovery_flow.py audio.wav \
      --user-id user123 \
      --enrollment-id enroll-456 \
      --recovery-type account_recovery \
      --email user@example.com

    # Account unlock after lockout
    python account_recovery_flow.py audio.wav \
      --user-id user123 \
      --enrollment-id enroll-456 \
      --recovery-type account_unlock
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import client (after path modification)
sys.path.insert(0, str(Path(__file__).parent))
from client import SonotheiaClient  # noqa: E402


class RecoveryType(str, Enum):
    """Account recovery types."""

    PASSWORD_RESET = "password_reset"
    ACCOUNT_RECOVERY = "account_recovery"
    ACCOUNT_UNLOCK = "account_unlock"
    EMAIL_CHANGE = "email_change"
    PHONE_CHANGE = "phone_change"


class AccountRecoveryFlow:
    """Account recovery flow handler with voice verification."""

    # Strict thresholds for account recovery (higher security)
    DEEPFAKE_THRESHOLD = 0.3
    MFA_CONFIDENCE_THRESHOLD = 0.8

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        require_mfa: bool = True,
    ):
        """
        Initialize account recovery flow.

        Args:
            api_key: Sonotheia API key
            api_url: Base API URL
            require_mfa: Require MFA for all recovery operations
        """
        self.client = SonotheiaClient(api_key=api_key, api_url=api_url)
        self.require_mfa = require_mfa

    def verify_recovery(
        self,
        audio_path: str | Path,
        user_id: str,
        enrollment_id: str,
        recovery_type: RecoveryType,
        email: str | None = None,
        phone: str | None = None,
        device_id: str | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """
        Verify account recovery request using voice authentication.

        Args:
            audio_path: Path to voice recording
            user_id: User identifier
            enrollment_id: Voice enrollment ID
            recovery_type: Type of recovery operation
            email: Email address (if changing)
            phone: Phone number (if changing)
            device_id: Device identifier
            ip_address: IP address

        Returns:
            Verification result with authorization decision
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Verifying {recovery_type.value} for user {user_id}")

        # Step 1: Deepfake detection (strict threshold for recovery)
        deepfake_metadata = {
            "user_id": user_id,
            "recovery_type": recovery_type.value,
            "email": email,
            "phone": phone,
            "device_id": device_id,
            "ip_address": ip_address,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }

        try:
            deepfake_result = self.client.detect_deepfake(
                str(audio_path), metadata=deepfake_metadata
            )
            logger.info(f"Deepfake detection: score={deepfake_result.get('score', 0):.2f}")
        except requests.RequestException as e:
            logger.error(f"Deepfake detection failed: {e}")
            return self._create_error_response(
                user_id, recovery_type, "deepfake_detection_failed", str(e)
            )

        # Step 2: Voice MFA verification (required)
        mfa_context = {
            "user_id": user_id,
            "recovery_type": recovery_type.value,
            "device_id": device_id,
            "ip_address": ip_address,
        }

        try:
            mfa_result = self.client.verify_mfa(str(audio_path), enrollment_id, context=mfa_context)
            logger.info(f"MFA verification: verified={mfa_result.get('verified', False)}")
        except requests.RequestException as e:
            logger.error(f"MFA verification failed: {e}")
            return self._create_error_response(
                user_id, recovery_type, "mfa_verification_failed", str(e)
            )

        # Step 3: Risk assessment
        deepfake_score = deepfake_result.get("score", 0.5)
        mfa_verified = mfa_result.get("verified", False)
        mfa_confidence = mfa_result.get("confidence", 0.0)

        # Step 4: Authorization decision
        authorization = self._make_authorization_decision(
            recovery_type=recovery_type,
            deepfake_score=deepfake_score,
            mfa_verified=mfa_verified,
            mfa_confidence=mfa_confidence,
        )

        # Step 5: Create audit log
        audit_log = {
            "user_id": user_id,
            "recovery_type": recovery_type.value,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "deepfake": {
                "score": deepfake_score,
                "label": deepfake_result.get("label", "unknown"),
            },
            "mfa": {
                "verified": mfa_verified,
                "confidence": mfa_confidence,
            },
            "authorization": authorization,
            "device_id": device_id,
            "ip_address": ip_address,
        }

        return {
            "user_id": user_id,
            "recovery_type": recovery_type.value,
            "authorized": authorization["authorized"],
            "reason": authorization["reason"],
            "deepfake": deepfake_result,
            "mfa": mfa_result,
            "risk_level": authorization["risk_level"],
            "requires_additional_verification": authorization["requires_additional_verification"],
            "audit_log": audit_log,
            "session_id": deepfake_result.get("session_id"),
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }

    def _make_authorization_decision(
        self,
        recovery_type: RecoveryType,
        deepfake_score: float,
        mfa_verified: bool,
        mfa_confidence: float,
    ) -> dict[str, Any]:
        """
        Make authorization decision for recovery operation.

        Args:
            recovery_type: Type of recovery operation
            deepfake_score: Deepfake detection score
            mfa_verified: Whether MFA verification passed
            mfa_confidence: MFA confidence score

        Returns:
            Authorization decision
        """
        # MFA is required - if it fails, deny
        if not mfa_verified:
            return {
                "authorized": False,
                "reason": "voice_mfa_verification_failed",
                "risk_level": "high",
                "requires_additional_verification": False,
            }

        # Low MFA confidence - deny for recovery operations
        if mfa_confidence < self.MFA_CONFIDENCE_THRESHOLD:
            return {
                "authorized": False,
                "reason": "insufficient_mfa_confidence",
                "risk_level": "high",
                "requires_additional_verification": False,
            }

        # High deepfake score - deny
        if deepfake_score > self.DEEPFAKE_THRESHOLD:
            return {
                "authorized": False,
                "reason": "high_deepfake_score",
                "risk_level": "high",
                "requires_additional_verification": False,
            }

        # Medium deepfake score - require additional verification
        if deepfake_score > self.DEEPFAKE_THRESHOLD * 0.7:
            return {
                "authorized": True,
                "reason": "approved_with_additional_verification",
                "risk_level": "medium",
                "requires_additional_verification": True,
            }

        # All checks passed
        return {
            "authorized": True,
            "reason": "approved",
            "risk_level": "low",
            "requires_additional_verification": False,
        }

    def _create_error_response(
        self, user_id: str, recovery_type: RecoveryType, error_type: str, error_message: str
    ) -> dict[str, Any]:
        """Create error response structure."""
        return {
            "user_id": user_id,
            "recovery_type": recovery_type.value,
            "authorized": False,
            "reason": error_type,
            "error": {
                "type": error_type,
                "message": error_message,
            },
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Account Recovery Flow Example")
    parser.add_argument("audio", type=Path, help="Path to voice recording")
    parser.add_argument("--user-id", required=True, help="User identifier")
    parser.add_argument("--enrollment-id", required=True, help="Voice enrollment ID")
    parser.add_argument(
        "--recovery-type",
        type=RecoveryType,
        required=True,
        choices=list(RecoveryType),
        help="Recovery type",
    )
    parser.add_argument("--email", help="Email address (if changing)")
    parser.add_argument("--phone", help="Phone number (if changing)")
    parser.add_argument("--device-id", help="Device identifier")
    parser.add_argument("--ip-address", help="IP address")
    parser.add_argument("--json", action="store_true", help="Output JSON format")

    args = parser.parse_args()

    # Initialize integration
    api_key = os.getenv("SONOTHEIA_API_KEY")
    api_url = os.getenv("SONOTHEIA_API_URL")

    recovery = AccountRecoveryFlow(api_key=api_key, api_url=api_url, require_mfa=True)

    # Verify recovery
    try:
        result = recovery.verify_recovery(
            audio_path=args.audio,
            user_id=args.user_id,
            enrollment_id=args.enrollment_id,
            recovery_type=args.recovery_type,
            email=args.email,
            phone=args.phone,
            device_id=args.device_id,
            ip_address=args.ip_address,
        )

        # Output result
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("\n[Recovery Verification Result]")
            print(f"User ID: {result['user_id']}")
            print(f"Recovery Type: {result['recovery_type']}")
            print(f"Authorized: {result['authorized']}")
            print(f"Reason: {result['reason']}")
            print(f"Risk Level: {result['risk_level']}")
            if result.get("requires_additional_verification"):
                print("⚠️  Additional verification required")

        # Exit code
        sys.exit(0 if result["authorized"] else 1)

    except Exception as e:
        logger.error(f"Error verifying recovery: {e}", exc_info=True)
        if args.json:
            print(json.dumps({"error": str(e), "user_id": args.user_id}, indent=2))
        else:
            print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
