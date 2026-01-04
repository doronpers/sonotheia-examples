"""
Voice integrity routing example for financial services.

This example demonstrates how to:
- Analyze voice calls for deepfake detection
- Make risk-based routing decisions
- Handle different confidence levels
- Implement step-up authentication logic
- Generate audit trails

Inspired by voice integrity control layers used in banking and financial services.

Usage:
    python voice_routing_example.py audio.wav --transaction-amount 50000
"""

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classification."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RoutingAction(Enum):
    """Routing decision actions."""
    ALLOW = "ALLOW"
    REQUIRE_CALLBACK = "REQUIRE_CALLBACK"
    REQUIRE_STEP_UP = "REQUIRE_STEP_UP"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"
    BLOCK = "BLOCK"


@dataclass
class TransactionContext:
    """Transaction context for risk assessment."""
    transaction_id: str
    customer_id: str
    amount_usd: float
    destination_country: str
    is_new_beneficiary: bool
    channel: str  # phone, web, mobile
    customer_risk_score: float = 0.0


@dataclass
class VoiceAnalysisResult:
    """Voice analysis result."""
    deepfake_score: float
    confidence: float
    risk_level: RiskLevel
    reason_codes: list[str]
    feature_contributions: Dict[str, float]
    session_id: str


@dataclass
class RoutingDecision:
    """Routing decision with audit trail."""
    action: RoutingAction
    risk_level: RiskLevel
    confidence: float
    reason: str
    requires_human_review: bool
    additional_controls: list[str]
    audit_trail: Dict[str, Any]


class VoiceIntegrityRouter:
    """Voice integrity routing engine for financial services."""

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.sonotheia.com"
    ):
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")

        # Configurable thresholds
        self.confidence_threshold = 0.6
        self.high_risk_score_threshold = 0.7
        self.medium_risk_score_threshold = 0.4
        self.high_value_transaction_threshold = 100000.0

    def analyze_voice(self, audio_path: str) -> VoiceAnalysisResult:
        """
        Analyze voice audio for deepfake detection.

        Args:
            audio_path: Path to audio file

        Returns:
            Voice analysis result
        """
        logger.info(f"Analyzing voice audio: {audio_path}")

        with open(audio_path, "rb") as f:
            files = {"audio": (Path(audio_path).name, f, "audio/wav")}

            response = requests.post(
                f"{self.api_url}/v1/voice/deepfake",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json",
                },
                files=files,
                timeout=30.0,
            )

        response.raise_for_status()
        result = response.json()

        # Map to risk level
        score = result.get("score", 0.0)
        if score > self.high_risk_score_threshold:
            risk_level = RiskLevel.HIGH
        elif score > self.medium_risk_score_threshold:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return VoiceAnalysisResult(
            deepfake_score=score,
            confidence=result.get("confidence", 0.0),
            risk_level=risk_level,
            reason_codes=result.get("reason_codes", []),
            feature_contributions=result.get("feature_contributions", {}),
            session_id=result.get("session_id", "unknown")
        )

    def make_routing_decision(
        self,
        voice_result: VoiceAnalysisResult,
        context: TransactionContext
    ) -> RoutingDecision:
        """
        Make routing decision based on voice analysis and transaction context.

        Args:
            voice_result: Voice analysis result
            context: Transaction context

        Returns:
            Routing decision
        """
        logger.info(f"Making routing decision for transaction {context.transaction_id}")

        # Calculate composite risk score
        composite_risk = self._calculate_composite_risk(voice_result, context)

        # Determine action
        action = self._determine_action(voice_result, context, composite_risk)

        # Determine additional controls needed
        additional_controls = self._determine_additional_controls(
            voice_result, context, action
        )

        # Build audit trail
        audit_trail = {
            "timestamp": datetime.utcnow().isoformat(),
            "transaction_id": context.transaction_id,
            "customer_id": context.customer_id,
            "voice_analysis": {
                "deepfake_score": voice_result.deepfake_score,
                "confidence": voice_result.confidence,
                "risk_level": voice_result.risk_level.value,
                "session_id": voice_result.session_id,
            },
            "transaction_context": {
                "amount_usd": context.amount_usd,
                "destination_country": context.destination_country,
                "is_new_beneficiary": context.is_new_beneficiary,
                "channel": context.channel,
            },
            "composite_risk_score": composite_risk,
            "decision": action.value,
        }

        # Generate decision reason
        reason = self._generate_decision_reason(
            voice_result, context, composite_risk, action
        )

        return RoutingDecision(
            action=action,
            risk_level=voice_result.risk_level,
            confidence=voice_result.confidence,
            reason=reason,
            requires_human_review=(action == RoutingAction.ESCALATE_TO_HUMAN),
            additional_controls=additional_controls,
            audit_trail=audit_trail
        )

    def _calculate_composite_risk(
        self,
        voice_result: VoiceAnalysisResult,
        context: TransactionContext
    ) -> float:
        """Calculate composite risk score."""
        # Base risk from voice analysis
        risk_score = voice_result.deepfake_score

        # Adjust for transaction factors
        if context.amount_usd > self.high_value_transaction_threshold:
            risk_score *= 1.2

        if context.is_new_beneficiary:
            risk_score *= 1.15

        if context.customer_risk_score > 0.5:
            risk_score *= 1.1

        # High-risk countries
        high_risk_countries = ["AF", "IR", "KP", "SY"]
        if context.destination_country in high_risk_countries:
            risk_score *= 1.3

        return min(risk_score, 1.0)

    def _determine_action(
        self,
        voice_result: VoiceAnalysisResult,
        context: TransactionContext,
        composite_risk: float
    ) -> RoutingAction:
        """Determine routing action."""
        # Low confidence always requires human review
        if voice_result.confidence < self.confidence_threshold:
            return RoutingAction.ESCALATE_TO_HUMAN

        # Critical risk cases
        if composite_risk > 0.85:
            return RoutingAction.BLOCK

        # High risk cases
        if voice_result.risk_level == RiskLevel.HIGH:
            if context.amount_usd > 50000:
                return RoutingAction.ESCALATE_TO_HUMAN
            else:
                return RoutingAction.REQUIRE_STEP_UP

        # Medium risk cases
        if voice_result.risk_level == RiskLevel.MEDIUM:
            if context.is_new_beneficiary or context.amount_usd > 25000:
                return RoutingAction.REQUIRE_CALLBACK
            else:
                return RoutingAction.REQUIRE_STEP_UP

        # Low risk - allow with standard controls
        return RoutingAction.ALLOW

    def _determine_additional_controls(
        self,
        voice_result: VoiceAnalysisResult,
        context: TransactionContext,
        action: RoutingAction
    ) -> list[str]:
        """Determine additional security controls needed."""
        controls = []

        if action == RoutingAction.REQUIRE_STEP_UP:
            controls.append("SMS_OTP")
            if context.amount_usd > 50000:
                controls.append("EMAIL_CONFIRMATION")

        elif action == RoutingAction.REQUIRE_CALLBACK:
            controls.append("OUTBOUND_CALLBACK")
            controls.append("VERIFY_TRANSACTION_DETAILS")

        elif action == RoutingAction.ESCALATE_TO_HUMAN:
            controls.append("FRAUD_TEAM_REVIEW")
            controls.append("CUSTOMER_INTERVIEW")

        # Always log high-risk transactions
        if voice_result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            controls.append("SAR_CONSIDERATION")

        return controls

    def _generate_decision_reason(
        self,
        voice_result: VoiceAnalysisResult,
        context: TransactionContext,
        composite_risk: float,
        action: RoutingAction
    ) -> str:
        """Generate human-readable decision reason."""
        reasons = []

        # Voice analysis factors
        if voice_result.deepfake_score > 0.7:
            reasons.append(f"High deepfake score ({voice_result.deepfake_score:.2f})")

        if voice_result.confidence < 0.6:
            reasons.append(f"Low confidence ({voice_result.confidence:.2f})")

        # Transaction factors
        if context.amount_usd > 100000:
            reasons.append(f"High-value transaction (${context.amount_usd:,.0f})")

        if context.is_new_beneficiary:
            reasons.append("New beneficiary")

        # Reason codes from voice analysis
        if voice_result.reason_codes:
            reasons.append(f"Voice anomalies: {', '.join(voice_result.reason_codes[:3])}")

        reason_text = "; ".join(reasons) if reasons else "Standard processing"

        return f"{action.value}: {reason_text}"


def print_routing_decision(decision: RoutingDecision):
    """Print routing decision in a readable format."""
    print("\n" + "=" * 70)
    print("ROUTING DECISION")
    print("=" * 70)
    print(f"Action:             {decision.action.value}")
    print(f"Risk Level:         {decision.risk_level.value}")
    print(f"Confidence:         {decision.confidence:.3f}")
    print(f"Human Review:       {'YES' if decision.requires_human_review else 'NO'}")
    print()
    print(f"Reason: {decision.reason}")
    print()

    if decision.additional_controls:
        print("Additional Controls Required:")
        for control in decision.additional_controls:
            print(f"  - {control}")
        print()

    print("=" * 70 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Voice integrity routing for financial services"
    )
    parser.add_argument("audio", help="Path to voice audio file")
    parser.add_argument(
        "--transaction-id",
        default=f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}",
        help="Transaction ID"
    )
    parser.add_argument("--customer-id", required=True, help="Customer ID")
    parser.add_argument(
        "--transaction-amount",
        type=float,
        required=True,
        help="Transaction amount in USD"
    )
    parser.add_argument(
        "--destination-country",
        default="US",
        help="Destination country code"
    )
    parser.add_argument(
        "--new-beneficiary",
        action="store_true",
        help="Transaction to new beneficiary"
    )
    parser.add_argument(
        "--channel",
        choices=["phone", "web", "mobile"],
        default="phone",
        help="Transaction channel"
    )
    parser.add_argument(
        "--customer-risk-score",
        type=float,
        default=0.0,
        help="Customer risk score (0.0-1.0)"
    )
    parser.add_argument("--api-key", help="API key")
    parser.add_argument("--api-url", default="https://api.sonotheia.com")
    parser.add_argument("--save-audit", help="Save audit trail to JSON file")

    args = parser.parse_args()

    # Get API key
    import os
    api_key = args.api_key or os.getenv("SONOTHEIA_API_KEY")
    if not api_key:
        logger.error("API key required. Set SONOTHEIA_API_KEY or use --api-key")
        sys.exit(1)

    # Create transaction context
    context = TransactionContext(
        transaction_id=args.transaction_id,
        customer_id=args.customer_id,
        amount_usd=args.transaction_amount,
        destination_country=args.destination_country,
        is_new_beneficiary=args.new_beneficiary,
        channel=args.channel,
        customer_risk_score=args.customer_risk_score
    )

    # Create router
    router = VoiceIntegrityRouter(api_key=api_key, api_url=args.api_url)

    try:
        # Analyze voice
        logger.info("Step 1: Analyzing voice audio...")
        voice_result = router.analyze_voice(args.audio)

        logger.info(f"Voice analysis complete: "
                   f"score={voice_result.deepfake_score:.3f}, "
                   f"confidence={voice_result.confidence:.3f}")

        # Make routing decision
        logger.info("Step 2: Making routing decision...")
        decision = router.make_routing_decision(voice_result, context)

        # Display decision
        print_routing_decision(decision)

        # Save audit trail if requested
        if args.save_audit:
            with open(args.save_audit, "w") as f:
                json.dump(decision.audit_trail, f, indent=2)
            logger.info(f"Audit trail saved to: {args.save_audit}")

        # Exit with appropriate code
        if decision.action == RoutingAction.BLOCK:
            sys.exit(2)
        elif decision.requires_human_review:
            sys.exit(1)
        else:
            sys.exit(0)

    except requests.HTTPError as e:
        logger.error(f"API Error: {e.response.status_code}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
