"""
Example demonstrating enhanced Sonotheia client features.

This example shows:
- Retry logic with exponential backoff
- Rate limiting
- Circuit breaker pattern
- Connection pooling
- Comprehensive error handling

Usage:
    SONOTHEIA_API_KEY=... python enhanced_example.py path/to/audio.wav
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

import requests

from client_enhanced import CircuitBreakerConfig, SonotheiaClientEnhanced

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enhanced Sonotheia API client example with retry and rate limiting"
    )
    parser.add_argument("audio", help="Path to WAV/Opus audio to submit")
    parser.add_argument(
        "--enrollment-id", help="Enrollment/voiceprint identifier for MFA verification"
    )
    parser.add_argument("--session-id", help="Session identifier to link SARs and risk events")
    parser.add_argument(
        "--decision", default="review", help="Decision for SAR submission (allow/deny/review)"
    )
    parser.add_argument(
        "--reason", default="Manual review requested", help="Human readable SAR reason"
    )
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum retry attempts")
    parser.add_argument("--rate-limit", type=float, help="Rate limit in requests per second")
    parser.add_argument(
        "--disable-circuit-breaker", action="store_true", help="Disable circuit breaker"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Configure circuit breaker
    circuit_config = CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60.0,
        success_threshold=2,
    )

    try:
        # Initialize enhanced client with production features
        with SonotheiaClientEnhanced(
            max_retries=args.max_retries,
            rate_limit_rps=args.rate_limit,
            enable_circuit_breaker=not args.disable_circuit_breaker,
            circuit_breaker_config=circuit_config,
        ) as client:
            logger.info(
                f"Initialized enhanced client (retries={args.max_retries}, "
                f"rate_limit={args.rate_limit or 'disabled'}, "
                f"circuit_breaker={'disabled' if args.disable_circuit_breaker else 'enabled'})"
            )

            results = {}

            # Always run deepfake detection
            logger.info(f"Running deepfake detection on {args.audio}")
            try:
                results["deepfake"] = client.detect_deepfake(
                    args.audio,
                    metadata={"session_id": args.session_id or "demo-session", "channel": "web"},
                )
                logger.info(
                    f"Deepfake detection result: score={results['deepfake'].get('score')}, "
                    f"label={results['deepfake'].get('label')}"
                )
            except requests.HTTPError as exc:
                error_detail = exc.response.text if hasattr(exc, "response") else str(exc)
                logger.error(f"Deepfake detection failed: {error_detail}")
                sys.exit(1)
            except Exception as exc:
                logger.error(f"Deepfake detection failed: {exc}")
                sys.exit(1)

            # Run MFA verification if enrollment ID provided
            if args.enrollment_id:
                logger.info(f"Running MFA verification for enrollment {args.enrollment_id}")
                try:
                    results["mfa"] = client.verify_mfa(
                        args.audio,
                        args.enrollment_id,
                        context={"session_id": args.session_id or "demo-session", "channel": "ivr"},
                    )
                    logger.info(
                        f"MFA verification result: verified={results['mfa'].get('verified')}, "
                        f"confidence={results['mfa'].get('confidence')}"
                    )
                except requests.HTTPError as exc:
                    error_detail = exc.response.text if hasattr(exc, "response") else str(exc)
                    logger.error(f"MFA verification failed: {error_detail}")
                    sys.exit(1)
                except Exception as exc:
                    logger.error(f"MFA verification failed: {exc}")
                    sys.exit(1)

            # Submit SAR if session ID provided
            if args.session_id:
                logger.info(f"Submitting SAR for session {args.session_id}")
                try:
                    results["sar"] = client.submit_sar(
                        args.session_id,
                        decision=args.decision,
                        reason=args.reason,
                        metadata={"source": "enhanced-example"},
                    )
                    logger.info(
                        f"SAR submission result: status={results['sar'].get('status')}, "
                        f"case_id={results['sar'].get('case_id')}"
                    )
                except requests.HTTPError as exc:
                    error_detail = exc.response.text if hasattr(exc, "response") else str(exc)
                    logger.error(f"SAR submission failed: {error_detail}")
                    sys.exit(1)
                except Exception as exc:
                    logger.error(f"SAR submission failed: {exc}")
                    sys.exit(1)

            print("\n=== Results ===")
            print(json.dumps(results, indent=2))

    except ValueError as exc:
        logger.error(f"Configuration error: {exc}")
        sys.exit(1)
    except Exception as exc:
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
