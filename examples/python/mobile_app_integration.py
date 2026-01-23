"""
Mobile App Integration Example

Demonstrates integration patterns for mobile applications (iOS/Android) using
voice fraud detection for account security and transaction verification.

Use Cases:
- Account login with voice verification
- Transaction authorization
- Password reset with voice MFA
- High-security operations (wire transfers, account changes)

Example Usage:
    # Account login verification
    python mobile_app_integration.py audio.wav \
      --user-id user123 \
      --enrollment-id enroll-456 \
      --operation login

    # Transaction authorization
    python mobile_app_integration.py audio.wav \
      --user-id user123 \
      --enrollment-id enroll-456 \
      --operation transaction \
      --transaction-id TXN789 \
      --amount 5000

    # Password reset with voice verification
    python mobile_app_integration.py audio.wav \
      --user-id user123 \
      --enrollment-id enroll-456 \
      --operation password_reset
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


class OperationType(str, Enum):
    """Supported operation types."""

    LOGIN = "login"
    TRANSACTION = "transaction"
    PASSWORD_RESET = "password_reset"
    ACCOUNT_CHANGE = "account_change"
    WIRE_TRANSFER = "wire_transfer"


class MobileAppIntegration:
    """Mobile app integration handler for voice-based security."""

    # Risk thresholds by operation
    RISK_THRESHOLDS = {
        OperationType.LOGIN: 0.6,
        OperationType.TRANSACTION: 0.5,
        OperationType.PASSWORD_RESET: 0.4,
        OperationType.ACCOUNT_CHANGE: 0.4,
        OperationType.WIRE_TRANSFER: 0.3,
    }

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        require_mfa: bool = True,
    ):
        """
        Initialize mobile app integration.

        Args:
            api_key: Sonotheia API key
            api_url: Base API URL
            require_mfa: Require MFA for all operations
        """
        self.client = SonotheiaClient(api_key=api_key, api_url=api_url)
        self.require_mfa = require_mfa

    def verify_operation(
        self,
        audio_path: str | Path,
        user_id: str,
        enrollment_id: str,
        operation: OperationType,
        transaction_id: str | None = None,
        amount: float | None = None,
        device_id: str | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """
        Verify a mobile app operation using voice authentication.

        Args:
            audio_path: Path to voice recording
            user_id: User identifier
            enrollment_id: Voice enrollment ID
            operation: Type of operation
            transaction_id: Transaction identifier (if applicable)
            amount: Transaction amount (if applicable)
            device_id: Device identifier
            ip_address: IP address

        Returns:
            Verification result with authorization decision
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Verifying {operation.value} operation for user {user_id}")

        # Step 1: Deepfake detection
        deepfake_metadata = {
            "user_id": user_id,
            "operation": operation.value,
            "transaction_id": transaction_id,
            "amount": amount,
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
                user_id, operation, "deepfake_detection_failed", str(e)
            )

        # Step 2: Voice MFA verification (required for all operations)
        mfa_context = {
            "user_id": user_id,
            "operation": operation.value,
            "transaction_id": transaction_id,
            "device_id": device_id,
            "ip_address": ip_address,
        }

        try:
            mfa_result = self.client.verify_mfa(str(audio_path), enrollment_id, context=mfa_context)
            logger.info(f"MFA verification: verified={mfa_result.get('verified', False)}")
        except requests.RequestException as e:
            logger.error(f"MFA verification failed: {e}")
            return self._create_error_response(
                user_id, operation, "mfa_verification_failed", str(e)
            )

        # Step 3: Risk assessment
        risk_threshold = self.RISK_THRESHOLDS.get(operation, 0.5)
        deepfake_score = deepfake_result.get("score", 0.5)
        mfa_verified = mfa_result.get("verified", False)
        mfa_confidence = mfa_result.get("confidence", 0.0)

        # Step 4: Authorization decision
        authorization = self._make_authorization_decision(
            operation=operation,
            deepfake_score=deepfake_score,
            mfa_verified=mfa_verified,
            mfa_confidence=mfa_confidence,
            risk_threshold=risk_threshold,
            amount=amount,
        )

        return {
            "user_id": user_id,
            "operation": operation.value,
            "authorized": authorization["authorized"],
            "reason": authorization["reason"],
            "deepfake": {
                "score": deepfake_score,
                "label": deepfake_result.get("label", "unknown"),
            },
            "mfa": {
                "verified": mfa_verified,
                "confidence": mfa_confidence,
            },
            "risk_level": authorization["risk_level"],
            "requires_additional_verification": authorization["requires_additional_verification"],
            "session_id": deepfake_result.get("session_id"),
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }

    def _make_authorization_decision(
        self,
        operation: OperationType,
        deepfake_score: float,
        mfa_verified: bool,
        mfa_confidence: float,
        risk_threshold: float,
        amount: float | None = None,
    ) -> dict[str, Any]:
        """
        Make authorization decision based on risk factors.

        Args:
            operation: Operation type
            deepfake_score: Deepfake detection score
            mfa_verified: Whether MFA verification passed
            mfa_confidence: MFA confidence score
            risk_threshold: Risk threshold for operation
            amount: Transaction amount (if applicable)

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

        # Low MFA confidence
        if mfa_confidence < 0.7:
            return {
                "authorized": False,
                "reason": "low_mfa_confidence",
                "risk_level": "medium",
                "requires_additional_verification": True,
            }

        # High deepfake score
        if deepfake_score > risk_threshold:
            return {
                "authorized": False,
                "reason": "high_deepfake_score",
                "risk_level": "high",
                "requires_additional_verification": False,
            }

        # Medium deepfake score - require additional verification
        if deepfake_score > risk_threshold * 0.7:
            return {
                "authorized": True,
                "reason": "approved_with_additional_verification",
                "risk_level": "medium",
                "requires_additional_verification": True,
            }

        # High-value transactions - stricter checks
        if amount and amount > 10000:
            if deepfake_score > 0.3 or mfa_confidence < 0.85:
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
        self, user_id: str, operation: OperationType, error_type: str, error_message: str
    ) -> dict[str, Any]:
        """Create error response structure."""
        return {
            "user_id": user_id,
            "operation": operation.value,
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
    parser = argparse.ArgumentParser(description="Mobile App Integration Example")
    parser.add_argument("audio", type=Path, help="Path to voice recording")
    parser.add_argument("--user-id", required=True, help="User identifier")
    parser.add_argument("--enrollment-id", required=True, help="Voice enrollment ID")
    parser.add_argument(
        "--operation",
        type=OperationType,
        required=True,
        choices=list(OperationType),
        help="Operation type",
    )
    parser.add_argument("--transaction-id", help="Transaction identifier")
    parser.add_argument("--amount", type=float, help="Transaction amount")
    parser.add_argument("--device-id", help="Device identifier")
    parser.add_argument("--ip-address", help="IP address")
    parser.add_argument("--json", action="store_true", help="Output JSON format")

    args = parser.parse_args()

    # Initialize integration
    api_key = os.getenv("SONOTHEIA_API_KEY")
    api_url = os.getenv("SONOTHEIA_API_URL")

    integration = MobileAppIntegration(api_key=api_key, api_url=api_url, require_mfa=True)

    # Verify operation
    try:
        result = integration.verify_operation(
            audio_path=args.audio,
            user_id=args.user_id,
            enrollment_id=args.enrollment_id,
            operation=args.operation,
            transaction_id=args.transaction_id,
            amount=args.amount,
            device_id=args.device_id,
            ip_address=args.ip_address,
        )

        # Output result
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("\n[Authorization Result]")
            print(f"User ID: {result['user_id']}")
            print(f"Operation: {result['operation']}")
            print(f"Authorized: {result['authorized']}")
            print(f"Reason: {result['reason']}")
            print(f"Risk Level: {result['risk_level']}")
            if result.get("requires_additional_verification"):
                print("⚠️  Additional verification required")

        # Exit code
        sys.exit(0 if result["authorized"] else 1)

    except Exception as e:
        logger.error(f"Error verifying operation: {e}", exc_info=True)
        if args.json:
            print(json.dumps({"error": str(e), "user_id": args.user_id}, indent=2))
        else:
            print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
