"""
Event-Driven Integration Example

Demonstrates integration with event-driven architectures using message queues
(RabbitMQ, AWS SQS, Kafka) for asynchronous voice fraud detection processing.

Use Cases:
- Microservices architecture integration
- Asynchronous processing pipelines
- Event sourcing patterns
- Message queue integration
- Pub/sub patterns

Example Usage:
    # Process event from message queue
    python event_driven_integration.py \
      --event-file event.json \
      --queue-type sqs

    # Simulate event processing
    python event_driven_integration.py \
      --audio audio.wav \
      --event-type transaction_verification \
      --customer-id CUST123 \
      --simulate
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


class QueueType(str, Enum):
    """Supported message queue types."""

    SQS = "sqs"
    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"
    REDIS = "redis"


class EventType(str, Enum):
    """Supported event types."""

    TRANSACTION_VERIFICATION = "transaction_verification"
    ACCOUNT_ACCESS = "account_access"
    PAYMENT_PROCESSING = "payment_processing"
    USER_REGISTRATION = "user_registration"


class EventDrivenIntegration:
    """Event-driven integration handler for message queue processing."""

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        queue_type: QueueType = QueueType.SQS,
    ):
        """
        Initialize event-driven integration.

        Args:
            api_key: Sonotheia API key
            api_url: Base API URL
            queue_type: Message queue type
        """
        self.client = SonotheiaClient(api_key=api_key, api_url=api_url)
        self.queue_type = queue_type

    def process_event(
        self, event: dict[str, Any], audio_path: str | Path | None = None
    ) -> dict[str, Any]:
        """
        Process an event from message queue.

        Args:
            event: Event payload from message queue
            audio_path: Path to audio file (if not in event)

        Returns:
            Processing result with decision
        """
        # Extract event data
        event_type = event.get("event_type")
        audio_url = event.get("audio_url")
        audio_path = audio_path or event.get("audio_path")

        if not audio_path and not audio_url:
            raise ValueError("Either audio_path or audio_url must be provided in event")

        # Download audio if URL provided
        if audio_url and not audio_path:
            audio_path = self._download_audio(audio_url)

        if audio_path is None:
            raise ValueError("audio_path is required")

        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Processing {event_type} event")

        # Step 1: Deepfake detection
        deepfake_metadata = {
            "event_type": event_type,
            "event_id": event.get("event_id"),
            "customer_id": event.get("customer_id"),
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            **event.get("metadata", {}),
        }

        try:
            deepfake_result = self.client.detect_deepfake(
                str(audio_path), metadata=deepfake_metadata
            )
        except requests.RequestException as e:
            logger.error(f"Deepfake detection failed: {e}")
            return self._create_error_response(event, "deepfake_detection_failed", str(e))

        # Step 2: MFA verification (if enrollment ID in event)
        mfa_result = None
        enrollment_id = event.get("enrollment_id")
        if enrollment_id:
            mfa_context = {
                "event_type": event_type,
                "event_id": event.get("event_id"),
                "customer_id": event.get("customer_id"),
                **event.get("context", {}),
            }

            try:
                mfa_result = self.client.verify_mfa(
                    str(audio_path), enrollment_id, context=mfa_context
                )
            except requests.RequestException as e:
                logger.warning(f"MFA verification failed: {e}")

        # Step 3: Make decision based on event type
        if event_type is None:
            raise ValueError("event_type is required in event")
        decision = self._make_event_decision(event_type, deepfake_result, mfa_result, event)

        # Step 4: Create result
        result = {
            "event_id": event.get("event_id"),
            "event_type": event_type,
            "status": "processed",
            "deepfake": deepfake_result,
            "mfa": mfa_result,
            "decision": decision,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }

        # Step 5: Publish result to output queue (if configured)
        output_queue = event.get("output_queue")
        if output_queue:
            self._publish_result(result, output_queue)

        return result

    def _make_event_decision(
        self,
        event_type: str,
        deepfake_result: dict[str, Any],
        mfa_result: dict[str, Any] | None,
        event: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Make decision based on event type and results.

        Args:
            event_type: Type of event
            deepfake_result: Deepfake detection result
            mfa_result: MFA verification result (optional)
            event: Original event payload

        Returns:
            Decision with action and metadata
        """
        deepfake_score = deepfake_result.get("score", 0.5)
        action = "APPROVE"
        reasons: list[str] = []

        # Event-specific thresholds
        thresholds = {
            EventType.TRANSACTION_VERIFICATION: 0.5,
            EventType.ACCOUNT_ACCESS: 0.4,
            EventType.PAYMENT_PROCESSING: 0.3,
            EventType.USER_REGISTRATION: 0.6,
        }

        threshold = thresholds.get(EventType(event_type), 0.5)

        # High deepfake score
        if deepfake_score > threshold:
            action = "REJECT"
            reasons.append("high_deepfake_score")

        # MFA failure
        if mfa_result and not mfa_result.get("verified", False):
            action = "REJECT"
            reasons.append("mfa_verification_failed")

        # Low MFA confidence
        if mfa_result and mfa_result.get("confidence", 0.0) < 0.7:
            if action == "APPROVE":
                action = "REQUIRE_ADDITIONAL_VERIFICATION"
            reasons.append("low_mfa_confidence")

        return {
            "action": action,
            "reasons": reasons,
            "risk_level": "high"
            if deepfake_score > threshold
            else "medium"
            if deepfake_score > 0.5
            else "low",
        }

    def _download_audio(self, audio_url: str) -> Path:
        """
        Download audio file from URL.

        Args:
            audio_url: URL to audio file

        Returns:
            Path to downloaded file
        """
        import tempfile

        response = requests.get(audio_url, timeout=30)
        response.raise_for_status()

        # Create temp file
        fd, temp_path = tempfile.mkstemp(suffix=".wav")
        try:
            with open(fd, "wb") as f:
                f.write(response.content)
            return Path(temp_path)
        except Exception:
            os.unlink(temp_path)
            raise

    def _publish_result(self, result: dict[str, Any], output_queue: str) -> None:
        """
        Publish result to output queue.

        Args:
            result: Processing result
            output_queue: Output queue identifier
        """
        # This is a placeholder - actual implementation would use queue-specific SDKs
        logger.info(f"Would publish result to {output_queue} (queue type: {self.queue_type.value})")
        # In production, this would use:
        # - boto3 for SQS
        # - pika for RabbitMQ
        # - kafka-python for Kafka
        # - redis-py for Redis

    def _create_error_response(
        self, event: dict[str, Any], error_type: str, error_message: str
    ) -> dict[str, Any]:
        """Create error response structure."""
        return {
            "event_id": event.get("event_id"),
            "event_type": event.get("event_type"),
            "status": "error",
            "error": {
                "type": error_type,
                "message": error_message,
            },
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }

    def simulate_event(
        self,
        audio_path: str | Path,
        event_type: EventType,
        customer_id: str | None = None,
        enrollment_id: str | None = None,
        **metadata: Any,
    ) -> dict[str, Any]:
        """
        Simulate event processing (for testing).

        Args:
            audio_path: Path to audio file
            event_type: Type of event
            customer_id: Customer identifier
            enrollment_id: Enrollment ID for MFA
            **metadata: Additional metadata

        Returns:
            Processing result
        """
        event = {
            "event_id": f"evt-{datetime.now(UTC).timestamp()}",
            "event_type": event_type.value,
            "customer_id": customer_id,
            "enrollment_id": enrollment_id,
            "audio_path": str(audio_path),
            "metadata": metadata,
        }

        return self.process_event(event, audio_path=audio_path)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Event-Driven Integration Example")
    parser.add_argument("--event-file", type=Path, help="Path to event JSON file")
    parser.add_argument("--audio", type=Path, help="Path to audio file (for simulation)")
    parser.add_argument(
        "--event-type",
        type=EventType,
        choices=list(EventType),
        help="Event type (for simulation)",
    )
    parser.add_argument("--customer-id", help="Customer ID (for simulation)")
    parser.add_argument("--enrollment-id", help="Enrollment ID (for simulation)")
    parser.add_argument(
        "--queue-type",
        type=QueueType,
        default=QueueType.SQS,
        choices=list(QueueType),
        help="Message queue type",
    )
    parser.add_argument("--simulate", action="store_true", help="Simulate event processing")
    parser.add_argument("--json", action="store_true", help="Output JSON format")

    args = parser.parse_args()

    # Initialize integration
    api_key = os.getenv("SONOTHEIA_API_KEY")
    api_url = os.getenv("SONOTHEIA_API_URL")

    integration = EventDrivenIntegration(
        api_key=api_key, api_url=api_url, queue_type=args.queue_type
    )

    try:
        if args.simulate:
            # Simulate event
            if not args.audio or not args.event_type:
                parser.error("--audio and --event-type required for simulation")

            result = integration.simulate_event(
                audio_path=args.audio,
                event_type=args.event_type,
                customer_id=args.customer_id,
                enrollment_id=args.enrollment_id,
            )
        elif args.event_file:
            # Process event from file
            event = json.loads(args.event_file.read_text())
            result = integration.process_event(event)
        else:
            parser.error("Either --event-file or --simulate with --audio required")

        # Output result
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("\n[Event Processing Result]")
            print(f"Event ID: {result.get('event_id')}")
            print(f"Event Type: {result.get('event_type')}")
            print(f"Status: {result.get('status')}")
            if "decision" in result:
                decision = result["decision"]
                print(f"Decision: {decision.get('action')}")
                print(f"Risk Level: {decision.get('risk_level')}")

        sys.exit(0)

    except Exception as e:
        logger.error(f"Error processing event: {e}", exc_info=True)
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
