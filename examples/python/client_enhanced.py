"""
Enhanced Sonotheia API client with retry logic, rate limiting, and circuit breaker.

This module extends the basic client with hardened features:
- Exponential backoff retry logic
- Rate limiting
- Circuit breaker pattern
- Connection pooling
- Detailed error handling
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

import requests
from client import SonotheiaClient
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures detected, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Failures before opening circuit
    recovery_timeout: float = 60.0  # Seconds before attempting recovery
    success_threshold: int = 2  # Successes in half-open before closing


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance."""

    def __init__(self, config: CircuitBreakerConfig | None = None):
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.config.recovery_timeout:
                logger.info("Circuit breaker entering HALF_OPEN state")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure()
            raise exc

    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                logger.info("Circuit breaker closing after successful recovery")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker reopening due to failure during recovery")
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.config.failure_threshold:
            logger.error(f"Circuit breaker opening after {self.failure_count} failures")
            self.state = CircuitState.OPEN


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, requests_per_second: float):
        self.requests_per_second = requests_per_second
        self.tokens = requests_per_second
        self.last_update = time.time()

    def acquire(self, tokens: int = 1) -> None:
        """Block until tokens are available."""
        while True:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(
                self.requests_per_second,
                self.tokens + elapsed * self.requests_per_second,
            )
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return

            # Wait for tokens to refill
            sleep_time = (tokens - self.tokens) / self.requests_per_second
            time.sleep(sleep_time)


class SonotheiaClientEnhanced(SonotheiaClient):
    """Enhanced Sonotheia API client with hardened features."""

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        deepfake_path: str | None = None,
        mfa_path: str | None = None,
        sar_path: str | None = None,
        timeout: int = 30,
        validate_responses: bool = True,
        max_retries: int = 3,
        rate_limit_rps: float | None = None,
        enable_circuit_breaker: bool = True,
        circuit_breaker_config: CircuitBreakerConfig | None = None,
    ):
        """
        Initialize enhanced Sonotheia API client.

        Args:
            api_key: API key for authentication
            api_url: Base API URL
            deepfake_path: Deepfake endpoint path
            mfa_path: MFA endpoint path
            sar_path: SAR endpoint path
            timeout: Request timeout in seconds
            validate_responses: Enable response validation (default: True)
            max_retries: Maximum number of retry attempts
            rate_limit_rps: Rate limit in requests per second (None to disable)
            enable_circuit_breaker: Enable circuit breaker pattern
            circuit_breaker_config: Circuit breaker configuration
        """
        super().__init__(
            api_key=api_key,
            api_url=api_url,
            deepfake_path=deepfake_path,
            mfa_path=mfa_path,
            sar_path=sar_path,
            timeout=timeout,
            validate_responses=validate_responses,
        )

        # Setup session with connection pooling and retry logic
        self.session = self._create_session(max_retries)

        # Rate limiting
        self.rate_limiter = RateLimiter(rate_limit_rps) if rate_limit_rps else None

        # Circuit breaker
        self.circuit_breaker = None
        if enable_circuit_breaker:
            self.circuit_breaker = CircuitBreaker(circuit_breaker_config)

    def _create_session(self, max_retries: int) -> requests.Session:
        """Create session with connection pooling and retry configuration."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,  # Exponential backoff: {backoff factor} * (2 ** (retry - 1))
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"],
            raise_on_status=False,
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20,
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    @contextmanager
    def _rate_limit(self):
        """Context manager for rate limiting."""
        if self.rate_limiter:
            self.rate_limiter.acquire()
        yield

    def _make_request(
        self,
        method: str,
        url: str,
        files: Optional[dict] = None,
        data: Optional[dict] = None,
        json_body: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Make HTTP request with circuit breaker and rate limiting."""
        with self._rate_limit():
            if self.circuit_breaker:
                return self.circuit_breaker.call(
                    self._execute_request,
                    method,
                    url,
                    files=files,
                    data=data,
                    json=json_body,
                )
            else:
                return self._execute_request(method, url, files=files, data=data, json=json_body)

    def _execute_request(
        self,
        method: str,
        url: str,
        files: Optional[dict] = None,
        data: Optional[dict] = None,
        json: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Execute HTTP request and handle errors."""
        start_time = time.time()
        try:
            # We must pass headers explicitly if they are not in session,
            # but session carries cookies etc.
            # Base class defines _headers(). We should use them.
            headers = self._headers()

            response = self.session.request(
                method,
                url,
                headers=headers,
                files=files,
                data=data,
                json=json,
                timeout=self.timeout,
            )
            duration = time.time() - start_time

            logger.debug(
                f"{method} {url} completed in {duration:.3f}s with status {response.status_code}"
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as exc:
            duration = time.time() - start_time
            logger.error(f"{method} {url} failed in {duration:.3f}s: {exc}")
            raise
        except requests.exceptions.RequestException as exc:
            duration = time.time() - start_time
            logger.error(f"{method} {url} failed in {duration:.3f}s: {exc}")
            raise

    def close(self):
        """Close the HTTP session."""
        if self.session:
            self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
