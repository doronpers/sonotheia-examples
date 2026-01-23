"""
E-commerce Fraud Prevention Example

Demonstrates integration with e-commerce platforms for fraud prevention during
checkout, account creation, and high-value transactions.

Use Cases:
- Checkout fraud detection
- Account creation verification
- High-value order protection
- Guest checkout risk assessment
- Account takeover prevention

Example Usage:
    # Checkout fraud detection
    python ecommerce_fraud_prevention.py audio.wav \
      --order-id ORD123 \
      --customer-id CUST456 \
      --order-amount 1500 \
      --payment-method credit_card

    # Account creation verification
    python ecommerce_fraud_prevention.py audio.wav \
      --order-id ORD123 \
      --new-account \
      --email user@example.com

    # High-value order with MFA
    python ecommerce_fraud_prevention.py audio.wav \
      --order-id ORD123 \
      --customer-id CUST456 \
      --order-amount 10000 \
      --enrollment-id enroll-789 \
      --require-mfa
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


class PaymentMethod(str, Enum):
    """Payment method types."""

    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    CRYPTOCURRENCY = "cryptocurrency"


class EcommerceFraudPrevention:
    """E-commerce fraud prevention handler."""

    # Risk thresholds
    HIGH_VALUE_THRESHOLD = 1000.0
    VERY_HIGH_VALUE_THRESHOLD = 5000.0
    DEEPFAKE_THRESHOLD = 0.6
    STRICT_DEEPFAKE_THRESHOLD = 0.4  # For high-value orders

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        enable_mfa: bool = True,
    ):
        """
        Initialize e-commerce fraud prevention.

        Args:
            api_key: Sonotheia API key
            api_url: Base API URL
            enable_mfa: Enable voice MFA for high-risk orders
        """
        self.client = SonotheiaClient(api_key=api_key, api_url=api_url)
        self.enable_mfa = enable_mfa

    def assess_order_risk(
        self,
        audio_path: str | Path,
        order_id: str,
        order_amount: float,
        customer_id: str | None = None,
        email: str | None = None,
        payment_method: PaymentMethod | None = None,
        enrollment_id: str | None = None,
        new_account: bool = False,
        require_mfa: bool = False,
        shipping_address: str | None = None,
        billing_address: str | None = None,
    ) -> dict[str, Any]:
        """
        Assess fraud risk for an e-commerce order.

        Args:
            audio_path: Path to voice recording
            order_id: Order identifier
            order_amount: Order amount
            customer_id: Customer identifier (if existing customer)
            email: Email address
            payment_method: Payment method
            enrollment_id: Voice enrollment ID (for MFA)
            new_account: Whether this is a new account
            require_mfa: Require MFA verification
            shipping_address: Shipping address
            billing_address: Billing address

        Returns:
            Risk assessment with fraud decision
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Assessing fraud risk for order {order_id}")

        # Step 1: Deepfake detection
        deepfake_metadata = {
            "order_id": order_id,
            "customer_id": customer_id,
            "email": email,
            "order_amount": order_amount,
            "payment_method": payment_method.value if payment_method else None,
            "new_account": new_account,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }

        try:
            deepfake_result = self.client.detect_deepfake(
                str(audio_path), metadata=deepfake_metadata
            )
            logger.info(f"Deepfake detection: score={deepfake_result.get('score', 0):.2f}")
        except requests.RequestException as e:
            logger.error(f"Deepfake detection failed: {e}")
            return self._create_error_response(order_id, "deepfake_detection_failed", str(e))

        # Step 2: MFA verification (if enabled and enrollment ID provided)
        mfa_result = None
        if (self.enable_mfa or require_mfa) and enrollment_id:
            mfa_context = {
                "order_id": order_id,
                "customer_id": customer_id,
                "order_amount": order_amount,
                "payment_method": payment_method.value if payment_method else None,
            }

            try:
                mfa_result = self.client.verify_mfa(
                    str(audio_path), enrollment_id, context=mfa_context
                )
                logger.info(f"MFA verification: verified={mfa_result.get('verified', False)}")
            except requests.RequestException as e:
                logger.warning(f"MFA verification failed: {e}")

        # Step 3: Fraud risk assessment
        fraud_assessment = self._assess_fraud_risk(
            deepfake_result=deepfake_result,
            mfa_result=mfa_result,
            order_amount=order_amount,
            new_account=new_account,
            payment_method=payment_method,
            require_mfa=require_mfa,
        )

        # Step 4: Create audit log
        audit_log = {
            "order_id": order_id,
            "customer_id": customer_id,
            "email": email,
            "order_amount": order_amount,
            "payment_method": payment_method.value if payment_method else None,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "deepfake": {
                "score": deepfake_result.get("score", 0.0),
                "label": deepfake_result.get("label", "unknown"),
            },
            "mfa": mfa_result,
            "fraud_assessment": fraud_assessment,
        }

        return {
            "order_id": order_id,
            "status": "assessed",
            "fraud_risk": fraud_assessment["risk_level"],
            "approved": fraud_assessment["approved"],
            "reason": fraud_assessment["reason"],
            "deepfake": deepfake_result,
            "mfa": mfa_result,
            "recommendations": fraud_assessment["recommendations"],
            "audit_log": audit_log,
        }

    def _assess_fraud_risk(
        self,
        deepfake_result: dict[str, Any],
        mfa_result: dict[str, Any] | None,
        order_amount: float,
        new_account: bool,
        payment_method: PaymentMethod | None,
        require_mfa: bool,
    ) -> dict[str, Any]:
        """
        Assess fraud risk based on multiple factors.

        Args:
            deepfake_result: Deepfake detection result
            mfa_result: MFA verification result (optional)
            order_amount: Order amount
            new_account: Whether this is a new account
            payment_method: Payment method
            require_mfa: Whether MFA was required

        Returns:
            Fraud assessment with decision and recommendations
        """
        deepfake_score = deepfake_result.get("score", 0.5)
        reasons: list[str] = []
        recommendations: list[str] = []
        risk_level = "low"
        approved = True

        # Determine threshold based on order amount
        threshold = (
            self.STRICT_DEEPFAKE_THRESHOLD
            if order_amount >= self.VERY_HIGH_VALUE_THRESHOLD
            else self.DEEPFAKE_THRESHOLD
        )

        # High deepfake score
        if deepfake_score > threshold:
            approved = False
            risk_level = "high"
            reasons.append("high_deepfake_score")
            recommendations.append("Block order and flag for manual review")

        # Medium deepfake score
        elif deepfake_score > threshold * 0.7:
            risk_level = "medium"
            reasons.append("elevated_deepfake_score")
            recommendations.append("Require additional verification")
            if not mfa_result:
                recommendations.append("Request voice MFA verification")

        # High-value orders
        if order_amount >= self.VERY_HIGH_VALUE_THRESHOLD:
            risk_level = "high" if risk_level == "medium" else risk_level
            reasons.append("very_high_value_order")
            recommendations.append("Require manager approval")
            if not mfa_result:
                recommendations.append("Require voice MFA verification")

        elif order_amount >= self.HIGH_VALUE_THRESHOLD:
            if risk_level == "low":
                risk_level = "medium"
            reasons.append("high_value_order")
            recommendations.append("Additional verification recommended")

        # New account
        if new_account:
            if risk_level == "low":
                risk_level = "medium"
            reasons.append("new_account")
            recommendations.append("Verify account details")
            if order_amount >= self.HIGH_VALUE_THRESHOLD:
                recommendations.append("Require identity verification")

        # MFA failure
        if mfa_result and not mfa_result.get("verified", False):
            approved = False
            risk_level = "high"
            reasons.append("mfa_verification_failed")
            recommendations.append("Block order - voice verification failed")

        # High-risk payment methods
        if payment_method in (PaymentMethod.CRYPTOCURRENCY, PaymentMethod.BANK_TRANSFER):
            if risk_level == "low":
                risk_level = "medium"
            reasons.append("high_risk_payment_method")
            recommendations.append("Additional verification for payment method")

        return {
            "risk_level": risk_level,
            "approved": approved,
            "reason": ", ".join(reasons) if reasons else "low_risk",
            "recommendations": recommendations,
            "fraud_score": deepfake_score,
        }

    def _create_error_response(
        self, order_id: str, error_type: str, error_message: str
    ) -> dict[str, Any]:
        """Create error response structure."""
        return {
            "order_id": order_id,
            "status": "error",
            "fraud_risk": "unknown",
            "approved": False,
            "reason": "processing_error",
            "error": {
                "type": error_type,
                "message": error_message,
            },
        }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="E-commerce Fraud Prevention Example")
    parser.add_argument("audio", type=Path, help="Path to voice recording")
    parser.add_argument("--order-id", required=True, help="Order identifier")
    parser.add_argument("--order-amount", type=float, required=True, help="Order amount")
    parser.add_argument("--customer-id", help="Customer identifier")
    parser.add_argument("--email", help="Email address")
    parser.add_argument(
        "--payment-method",
        type=PaymentMethod,
        choices=list(PaymentMethod),
        help="Payment method",
    )
    parser.add_argument("--enrollment-id", help="Voice enrollment ID for MFA")
    parser.add_argument("--new-account", action="store_true", help="New account creation")
    parser.add_argument("--require-mfa", action="store_true", help="Require MFA verification")
    parser.add_argument("--shipping-address", help="Shipping address")
    parser.add_argument("--billing-address", help="Billing address")
    parser.add_argument("--json", action="store_true", help="Output JSON format")

    args = parser.parse_args()

    # Initialize integration
    api_key = os.getenv("SONOTHEIA_API_KEY")
    api_url = os.getenv("SONOTHEIA_API_URL")

    prevention = EcommerceFraudPrevention(api_key=api_key, api_url=api_url, enable_mfa=True)

    # Assess order risk
    try:
        result = prevention.assess_order_risk(
            audio_path=args.audio,
            order_id=args.order_id,
            order_amount=args.order_amount,
            customer_id=args.customer_id,
            email=args.email,
            payment_method=args.payment_method,
            enrollment_id=args.enrollment_id,
            new_account=args.new_account,
            require_mfa=args.require_mfa,
            shipping_address=args.shipping_address,
            billing_address=args.billing_address,
        )

        # Output result
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("\n[Fraud Assessment Result]")
            print(f"Order ID: {result['order_id']}")
            print(f"Fraud Risk: {result['fraud_risk'].upper()}")
            print(f"Approved: {result['approved']}")
            print(f"Reason: {result['reason']}")
            if result.get("recommendations"):
                print("\nRecommendations:")
                for rec in result["recommendations"]:
                    print(f"  • {rec}")  # noqa: F541

        # Exit code
        sys.exit(0 if result["approved"] else 1)

    except Exception as e:
        logger.error(f"Error assessing order risk: {e}", exc_info=True)
        if args.json:
            print(json.dumps({"error": str(e), "order_id": args.order_id}, indent=2))
        else:
            print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
