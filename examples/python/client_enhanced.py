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

import json
import logging
import mimetypes
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failures detected, requests blocked
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
                self.tokens + elapsed * self.requests_per_second
            )
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return

            # Wait for tokens to refill
            sleep_time = (tokens - self.tokens) / self.requests_per_second
            time.sleep(sleep_time)


class SonotheiaClientEnhanced:
    """Enhanced Sonotheia API client with hardened features."""

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        deepfake_path: str | None = None,
        mfa_path: str | None = None,
        sar_path: str | None = None,
        timeout: int = 30,
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
            max_retries: Maximum number of retry attempts
            rate_limit_rps: Rate limit in requests per second (None to disable)
            enable_circuit_breaker: Enable circuit breaker pattern
            circuit_breaker_config: Circuit breaker configuration
        """
        self.api_key = api_key or os.getenv("SONOTHEIA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Set SONOTHEIA_API_KEY environment variable or pass api_key parameter."
            )

        self.api_url = (api_url or os.getenv("SONOTHEIA_API_URL", "https://api.sonotheia.com")).rstrip("/")
        self.deepfake_path = deepfake_path or os.getenv("SONOTHEIA_DEEPFAKE_PATH", "/v1/voice/deepfake")
        self.mfa_path = mfa_path or os.getenv("SONOTHEIA_MFA_PATH", "/v1/mfa/voice/verify")
        self.sar_path = sar_path or os.getenv("SONOTHEIA_SAR_PATH", "/v1/reports/sar")
        self.timeout = timeout

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

    def _headers(self) -> dict[str, str]:
        """Get common request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

    @contextmanager
    def _rate_limit(self):
        """Context manager for rate limiting."""
        if self.rate_limiter:
            self.rate_limiter.acquire()
        yield

    def _audio_part(self, audio_path: str) -> tuple[str, Any, str]:
        """
        Prepare audio file part for multipart upload.

        Args:
            audio_path: Path to audio file

        Returns:
            Tuple of (filename, file_handle, mime_type)
        """
        mime_type, _ = mimetypes.guess_type(audio_path)
        return (
            os.path.basename(audio_path),
            open(audio_path, "rb"),
            mime_type or "application/octet-stream",
        )

    def _make_request(self, method: str, *args, **kwargs) -> dict[str, Any]:
        """Make HTTP request with circuit breaker and rate limiting."""
        with self._rate_limit():
            if self.circuit_breaker:
                return self.circuit_breaker.call(self._execute_request, method, *args, **kwargs)
            else:
                return self._execute_request(method, *args, **kwargs)

    def _execute_request(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        """Execute HTTP request and handle errors."""
        start_time = time.time()
        try:
            response = self.session.request(method, url, **kwargs)
            duration = time.time() - start_time

            logger.debug(f"{method} {url} completed in {duration:.3f}s with status {response.status_code}")

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

    def detect_deepfake(
        self, audio_path: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Detect if audio contains a deepfake.

        Args:
            audio_path: Path to audio file (WAV, Opus, MP3, or FLAC)
            metadata: Optional metadata dict (e.g., session_id, channel)

        Returns:
            Response dict with keys: score, label, latency_ms, session_id (optional)

        Raises:
            requests.HTTPError: If API returns an error status code
            requests.RequestException: For network/connection errors
        """
        url = f"{self.api_url}{self.deepfake_path}"

        with open(audio_path, "rb"):
            files = {"audio": self._audio_part(audio_path)}
            data = {"metadata": json.dumps(metadata or {})}

            return self._make_request(
                "POST",
                url,
                headers=self._headers(),
                files=files,
                data=data,
                timeout=self.timeout,
            )

    def verify_mfa(
        self,
        audio_path: str,
        enrollment_id: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Verify caller identity via voice MFA.

        Args:
            audio_path: Path to audio file
            enrollment_id: Enrollment/voiceprint identifier for the caller
            context: Optional context dict (e.g., session_id, channel)

        Returns:
            Response dict with keys: verified, enrollment_id, confidence, session_id (optional)

        Raises:
            requests.HTTPError: If API returns an error status code
            requests.RequestException: For network/connection errors
        """
        url = f"{self.api_url}{self.mfa_path}"

        with open(audio_path, "rb"):
            files = {"audio": self._audio_part(audio_path)}
            data = {
                "enrollment_id": enrollment_id,
                "context": json.dumps(context or {}),
            }

            return self._make_request(
                "POST",
                url,
                headers=self._headers(),
                files=files,
                data=data,
                timeout=self.timeout,
            )

    def submit_sar(
        self,
        session_id: str,
        decision: str,
        reason: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Submit a Suspicious Activity Report (SAR).

        Args:
            session_id: Session identifier to link with prior API calls
            decision: Decision type - 'allow', 'deny', or 'review'
            reason: Human-readable reason for the SAR
            metadata: Optional metadata dict

        Returns:
            Response dict with keys: status, case_id, session_id

        Raises:
            requests.HTTPError: If API returns an error status code
            requests.RequestException: For network/connection errors
        """
        url = f"{self.api_url}{self.sar_path}"

        payload = {
            "session_id": session_id,
            "decision": decision,
            "reason": reason,
            "metadata": metadata or {},
        }

        return self._make_request(
            "POST",
            url,
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )

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
