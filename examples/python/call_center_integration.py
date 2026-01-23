"""
Call Center / IVR Integration Example

Demonstrates integration with call center systems and IVR platforms for real-time
voice fraud detection during customer service calls.

Use Cases:
- Real-time deepfake detection during live calls
- Voice MFA verification for account access
- Risk-based call routing and escalation
- Compliance logging for regulated industries

Example Usage:
    # Basic call center integration
    python call_center_integration.py audio.wav --call-id CALL123 --agent-id AGENT456

    # With customer context
    python call_center_integration.py audio.wav \
      --call-id CALL123 \
      --customer-id CUST789 \
      --account-balance 50000 \
      --transaction-type withdrawal

    # High-risk transaction with MFA
    python call_center_integration.py audio.wav \
      --call-id CALL123 \
      --customer-id CUST789 \
      --enrollment-id enroll-123 \
      --transaction-amount 100000 \
      --require-mfa
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import UTC, datetime
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


class CallCenterIntegration:
    """Call center integration handler for real-time voice fraud detection."""

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        enable_mfa: bool = True,
        risk_threshold: float = 0.7,
    ):
        """
        Initialize call center integration.

        Args:
            api_key: Sonotheia API key
            api_url: Base API URL
            enable_mfa: Enable voice MFA verification
            risk_threshold: Deepfake score threshold for escalation
        """
        self.client = SonotheiaClient(api_key=api_key, api_url=api_url)
        self.enable_mfa = enable_mfa
        self.risk_threshold = risk_threshold
        self.call_logs: list[dict[str, Any]] = []

    def process_call(
        self,
        audio_path: str | Path,
        call_id: str,
        customer_id: str | None = None,
        agent_id: str | None = None,
        enrollment_id: str | None = None,
        transaction_amount: float | None = None,
        transaction_type: str | None = None,
        account_balance: float | None = None,
        require_mfa: bool = False,
    ) -> dict[str, Any]:
        """
        Process a call center interaction with voice fraud detection.

        Args:
            audio_path: Path to call audio recording
            call_id: Unique call identifier
            customer_id: Customer identifier
            agent_id: Agent identifier
            enrollment_id: Voice enrollment ID for MFA
            transaction_amount: Transaction amount (if applicable)
            transaction_type: Type of transaction
            account_balance: Account balance (for risk assessment)
            require_mfa: Force MFA verification

        Returns:
            Processing result with routing decision and audit trail
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Processing call {call_id}")

        # Step 1: Deepfake detection
        deepfake_metadata = {
            "call_id": call_id,
            "customer_id": customer_id,
            "agent_id": agent_id,
            "transaction_amount": transaction_amount,
            "transaction_type": transaction_type,
            "account_balance": account_balance,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }

        try:
            deepfake_result = self.client.detect_deepfake(
                str(audio_path), metadata=deepfake_metadata
            )
            logger.info(f"Deepfake detection: score={deepfake_result.get('score', 0):.2f}")
        except requests.RequestException as e:
            logger.error(f"Deepfake detection failed: {e}")
            return self._create_error_response(call_id, "deepfake_detection_failed", str(e))

        # Step 2: MFA verification (if enabled and enrollment ID provided)
        mfa_result = None
        if (self.enable_mfa or require_mfa) and enrollment_id:
            mfa_context = {
                "call_id": call_id,
                "customer_id": customer_id,
                "transaction_amount": transaction_amount,
                "transaction_type": transaction_type,
            }

            try:
                mfa_result = self.client.verify_mfa(
                    str(audio_path), enrollment_id, context=mfa_context
                )
                logger.info(f"MFA verification: verified={mfa_result.get('verified', False)}")
            except requests.RequestException as e:
                logger.warning(f"MFA verification failed: {e}")
                # Continue processing even if MFA fails

        # Step 3: Risk assessment and routing decision
        routing_decision = self._make_routing_decision(
            deepfake_result,
            mfa_result,
            transaction_amount=transaction_amount,
            account_balance=account_balance,
            require_mfa=require_mfa,
        )

        # Step 4: Create audit log
        audit_log = {
            "call_id": call_id,
            "customer_id": customer_id,
            "agent_id": agent_id,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "deepfake": {
                "score": deepfake_result.get("score", 0.0),
                "label": deepfake_result.get("label", "unknown"),
                "latency_ms": deepfake_result.get("latency_ms", 0),
            },
            "mfa": mfa_result,
            "routing_decision": routing_decision,
            "transaction": {
                "amount": transaction_amount,
                "type": transaction_type,
                "account_balance": account_balance,
            },
        }

        self.call_logs.append(audit_log)

        # Step 5: SAR submission (if high risk)
        sar_result = None
        if routing_decision["should_submit_sar"]:
            try:
                sar_result = self.client.submit_sar(
                    session_id=deepfake_result.get("session_id", call_id),
                    decision="review",
                    reason=routing_decision["sar_reason"],
                    metadata={
                        "call_id": call_id,
                        "customer_id": customer_id,
                        "deepfake_score": deepfake_result.get("score", 0.0),
                        "mfa_verified": mfa_result.get("verified", False) if mfa_result else None,
                    },
                )
                logger.info(f"SAR submitted: case_id={sar_result.get('case_id')}")
            except requests.RequestException as e:
                logger.warning(f"SAR submission failed: {e}")

        return {
            "call_id": call_id,
            "status": "processed",
            "deepfake": deepfake_result,
            "mfa": mfa_result,
            "routing_decision": routing_decision,
            "sar": sar_result,
            "audit_log": audit_log,
        }

    def _make_routing_decision(
        self,
        deepfake_result: dict[str, Any],
        mfa_result: dict[str, Any] | None,
        transaction_amount: float | None = None,
        account_balance: float | None = None,
        require_mfa: bool = False,
    ) -> dict[str, Any]:
        """
        Make routing decision based on risk factors.

        Args:
            deepfake_result: Deepfake detection result
            mfa_result: MFA verification result (optional)
            transaction_amount: Transaction amount
            account_balance: Account balance
            require_mfa: Whether MFA was required

        Returns:
            Routing decision with action and reasons
        """
        deepfake_score = deepfake_result.get("score", 0.5)
        reasons: list[str] = []
        action = "ALLOW"
        should_submit_sar = False
        sar_reason = ""

        # High deepfake score
        if deepfake_score > self.risk_threshold:
            action = "ESCALATE_TO_SUPERVISOR"
            reasons.append("high_deepfake_score")
            should_submit_sar = True
            sar_reason = f"High deepfake score detected: {deepfake_score:.2f}"

        # MFA failure
        if mfa_result and not mfa_result.get("verified", False):
            if action == "ALLOW":
                action = "REQUIRE_ADDITIONAL_VERIFICATION"
            else:
                action = "ESCALATE_TO_SUPERVISOR"
            reasons.append("mfa_verification_failed")
            should_submit_sar = True
            sar_reason = "Voice MFA verification failed"

        # High-value transaction
        if transaction_amount and transaction_amount > 10000:
            if deepfake_score > 0.5:
                action = "REQUIRE_MANAGER_APPROVAL"
                reasons.append("high_value_transaction")
            if transaction_amount > 50000:
                should_submit_sar = True
                sar_reason = f"High-value transaction: ${transaction_amount:,.2f}"

        # Account balance check
        if account_balance and transaction_amount:
            if transaction_amount > account_balance * 0.5:  # >50% of balance
                reasons.append("large_percentage_withdrawal")
                if action == "ALLOW":
                    action = "REQUIRE_ADDITIONAL_VERIFICATION"

        return {
            "action": action,
            "reasons": reasons,
            "should_submit_sar": should_submit_sar,
            "sar_reason": sar_reason,
            "risk_level": "high"
            if deepfake_score > self.risk_threshold
            else "medium"
            if deepfake_score > 0.5
            else "low",
        }

    def _create_error_response(
        self, call_id: str, error_type: str, error_message: str
    ) -> dict[str, Any]:
        """Create error response structure."""
        return {
            "call_id": call_id,
            "status": "error",
            "error": {
                "type": error_type,
                "message": error_message,
            },
            "routing_decision": {
                "action": "ESCALATE_TO_SUPERVISOR",
                "reasons": ["processing_error"],
            },
        }

    def export_audit_logs(self, output_path: str | Path) -> None:
        """Export call logs to JSON file."""
        output_path = Path(output_path)
        output_path.write_text(json.dumps(self.call_logs, indent=2))
        logger.info(f"Exported {len(self.call_logs)} call log(s) to {output_path}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Call Center Integration Example")
    parser.add_argument("audio", type=Path, help="Path to call audio file")
    parser.add_argument("--call-id", required=True, help="Unique call identifier")
    parser.add_argument("--customer-id", help="Customer identifier")
    parser.add_argument("--agent-id", help="Agent identifier")
    parser.add_argument("--enrollment-id", help="Voice enrollment ID for MFA")
    parser.add_argument("--transaction-amount", type=float, help="Transaction amount")
    parser.add_argument("--transaction-type", help="Type of transaction")
    parser.add_argument("--account-balance", type=float, help="Account balance")
    parser.add_argument("--require-mfa", action="store_true", help="Require MFA verification")
    parser.add_argument(
        "--risk-threshold", type=float, default=0.7, help="Risk threshold for escalation"
    )
    parser.add_argument("--export-logs", type=Path, help="Export audit logs to file")
    parser.add_argument("--json", action="store_true", help="Output JSON format")

    args = parser.parse_args()

    # Initialize integration
    api_key = os.getenv("SONOTHEIA_API_KEY")
    api_url = os.getenv("SONOTHEIA_API_URL")

    integration = CallCenterIntegration(
        api_key=api_key,
        api_url=api_url,
        enable_mfa=True,
        risk_threshold=args.risk_threshold,
    )

    # Process call
    try:
        result = integration.process_call(
            audio_path=args.audio,
            call_id=args.call_id,
            customer_id=args.customer_id,
            agent_id=args.agent_id,
            enrollment_id=args.enrollment_id,
            transaction_amount=args.transaction_amount,
            transaction_type=args.transaction_type,
            account_balance=args.account_balance,
            require_mfa=args.require_mfa,
        )

        # Export logs if requested
        if args.export_logs:
            integration.export_audit_logs(args.export_logs)

        # Output result
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("\n[Call Processing Result]")
            print(f"Call ID: {result['call_id']}")
            print(f"Status: {result['status']}")
            if "deepfake" in result:
                print(f"Deepfake Score: {result['deepfake'].get('score', 0):.2f}")
            if "mfa" in result and result["mfa"]:
                print(f"MFA Verified: {result['mfa'].get('verified', False)}")
            if "routing_decision" in result:
                decision = result["routing_decision"]
                print(f"Routing Action: {decision.get('action')}")
                print(f"Risk Level: {decision.get('risk_level')}")
                if decision.get("reasons"):
                    print(f"Reasons: {', '.join(decision['reasons'])}")

        # Exit code based on routing decision
        if result.get("status") == "error":
            sys.exit(1)
        elif result.get("routing_decision", {}).get("action") in (
            "ESCALATE_TO_SUPERVISOR",
            "BLOCK",
        ):
            sys.exit(2)  # High risk
        else:
            sys.exit(0)

    except Exception as e:
        logger.error(f"Error processing call: {e}", exc_info=True)
        if args.json:
            print(json.dumps({"error": str(e), "call_id": args.call_id}, indent=2))
        else:
            print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
