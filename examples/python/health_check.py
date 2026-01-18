"""
Health check and monitoring utilities for Sonotheia API integration.

This module provides:
- API health checks
- Connection validation
- Metrics collection
- Readiness probes for Kubernetes/container orchestration

Usage:
    # Simple health check
    python health_check.py

    # Continuous monitoring
    python health_check.py --monitor --interval 60

    # Export metrics for Prometheus
    python health_check.py --prometheus-port 9090
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Health check result."""

    timestamp: str
    healthy: bool
    latency_ms: float
    status_code: int | None = None
    error: str | None = None
    details: dict[str, Any] | None = None


class SonotheiaHealthChecker:
    """Health checker for Sonotheia API."""

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.sonotheia.com",
        timeout: int = 10,
    ):
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout

    def check_connectivity(self) -> HealthCheckResult:
        """
        Check basic connectivity to API.

        Returns:
            HealthCheckResult with connection status
        """
        start_time = time.time()
        timestamp = datetime.utcnow().isoformat()

        try:
            # Try to reach the API base URL or a health endpoint if available
            # Note: Adjust this based on actual API health endpoint
            response = requests.get(
                f"{self.api_url}/health",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json",
                },
                timeout=self.timeout,
            )

            latency_ms = (time.time() - start_time) * 1000

            return HealthCheckResult(
                timestamp=timestamp,
                healthy=response.status_code == 200,
                latency_ms=latency_ms,
                status_code=response.status_code,
                details=response.json() if response.ok else None,
            )

        except requests.exceptions.RequestException as exc:
            latency_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                timestamp=timestamp,
                healthy=False,
                latency_ms=latency_ms,
                error=str(exc),
            )

    def check_authentication(self) -> HealthCheckResult:
        """
        Verify API key is valid.

        Returns:
            HealthCheckResult with authentication status
        """
        start_time = time.time()
        timestamp = datetime.utcnow().isoformat()

        try:
            # Attempt a minimal API call to verify authentication
            # Using HEAD request if supported, or GET with minimal data
            response = requests.head(
                f"{self.api_url}/v1/voice/deepfake",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                },
                timeout=self.timeout,
            )

            latency_ms = (time.time() - start_time) * 1000

            # 401 means bad auth, 405 means endpoint doesn't support HEAD but auth worked
            healthy = response.status_code != 401

            return HealthCheckResult(
                timestamp=timestamp,
                healthy=healthy,
                latency_ms=latency_ms,
                status_code=response.status_code,
                details={"authenticated": healthy},
            )

        except requests.exceptions.RequestException as exc:
            latency_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                timestamp=timestamp,
                healthy=False,
                latency_ms=latency_ms,
                error=str(exc),
            )

    def full_health_check(self) -> dict[str, HealthCheckResult]:
        """
        Perform comprehensive health check.

        Returns:
            Dictionary of check name to result
        """
        results = {
            "connectivity": self.check_connectivity(),
            "authentication": self.check_authentication(),
        }

        return results

    def is_healthy(self) -> bool:
        """
        Quick health check for readiness probes.

        Returns:
            True if service is healthy
        """
        result = self.check_authentication()
        return result.healthy


def export_prometheus_metrics(checker: SonotheiaHealthChecker, port: int = 9090):
    """
    Export metrics in Prometheus format.

    Args:
        checker: Health checker instance
        port: Port to listen on
    """
    try:
        from prometheus_client import Counter, Gauge, start_http_server
    except ImportError:
        logger.error("prometheus_client not installed. Install with: pip install prometheus-client")
        sys.exit(1)

    # Define metrics
    health_status = Gauge("sonotheia_api_health", "API health status (1=healthy, 0=unhealthy)")
    latency = Gauge("sonotheia_api_latency_ms", "API latency in milliseconds")
    check_counter = Counter("sonotheia_api_checks_total", "Total number of health checks")
    error_counter = Counter("sonotheia_api_errors_total", "Total number of errors")

    # Start metrics server
    start_http_server(port)
    logger.info(f"Prometheus metrics server started on port {port}")

    # Continuous monitoring
    while True:
        try:
            result = checker.check_connectivity()
            check_counter.inc()

            health_status.set(1 if result.healthy else 0)
            latency.set(result.latency_ms)

            if not result.healthy:
                error_counter.inc()
                logger.warning(f"Health check failed: {result.error}")
            else:
                logger.debug(f"Health check passed: {result.latency_ms:.2f}ms")

        except Exception as exc:
            logger.error(f"Health check error: {exc}")
            error_counter.inc()
            health_status.set(0)

        time.sleep(30)  # Check every 30 seconds


def monitor_continuous(checker: SonotheiaHealthChecker, interval: int = 60):
    """
    Continuously monitor API health.

    Args:
        checker: Health checker instance
        interval: Seconds between checks
    """
    logger.info(f"Starting continuous monitoring (interval: {interval}s)")

    while True:
        try:
            results = checker.full_health_check()

            all_healthy = all(r.healthy for r in results.values())
            status = "HEALTHY" if all_healthy else "UNHEALTHY"

            logger.info(f"Health check: {status}")
            for check_name, result in results.items():
                if result.healthy:
                    logger.info(f"  {check_name}: OK ({result.latency_ms:.2f}ms)")
                else:
                    logger.error(f"  {check_name}: FAILED - {result.error}")

            if not all_healthy:
                # Could send alert here
                logger.warning("API health check failed - consider alerting")

        except Exception as exc:
            logger.error(f"Monitoring error: {exc}")

        time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sonotheia API health checker")
    parser.add_argument("--api-key", help="API key (defaults to SONOTHEIA_API_KEY env var)")
    parser.add_argument("--api-url", default="https://api.sonotheia.com", help="API base URL")
    parser.add_argument("--monitor", action="store_true", help="Continuous monitoring mode")
    parser.add_argument("--interval", type=int, default=60, help="Monitoring interval in seconds")
    parser.add_argument(
        "--prometheus-port", type=int, help="Export Prometheus metrics on this port"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get API key
    import os

    api_key = args.api_key or os.getenv("SONOTHEIA_API_KEY")
    if not api_key:
        logger.error("API key required. Set SONOTHEIA_API_KEY or use --api-key")
        sys.exit(1)

    # Create health checker
    checker = SonotheiaHealthChecker(api_key, args.api_url)

    # Prometheus metrics mode
    if args.prometheus_port:
        export_prometheus_metrics(checker, args.prometheus_port)
        return

    # Continuous monitoring mode
    if args.monitor:
        monitor_continuous(checker, args.interval)
        return

    # Single health check
    results = checker.full_health_check()

    print("\n=== Sonotheia API Health Check ===\n")
    all_healthy = True
    for check_name, result in results.items():
        status = "✓ PASS" if result.healthy else "✗ FAIL"
        print(f"{check_name}: {status} ({result.latency_ms:.2f}ms)")
        if not result.healthy:
            all_healthy = False
            if result.error:
                print(f"  Error: {result.error}")

    print("\n" + json.dumps({k: asdict(v) for k, v in results.items()}, indent=2))

    sys.exit(0 if all_healthy else 1)


if __name__ == "__main__":
    main()
