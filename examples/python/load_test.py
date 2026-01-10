"""
Performance and load testing for Sonotheia API.

This script performs load tests to measure API performance under various conditions:
- Concurrent requests
- Sustained load
- Spike testing
- Stress testing

Requirements:
    pip install locust requests

Usage:
    # Run with Locust web interface
    locust -f load_test.py --host=https://api.sonotheia.com

    # Run headless with specific parameters
    locust -f load_test.py --host=https://api.sonotheia.com --users 10 --spawn-rate 2 --run-time 1m --headless

    # Custom scenarios
    python load_test.py --scenario sustained --users 50 --duration 300
    python load_test.py --scenario spike --users 100 --duration 60
    python load_test.py --scenario stress --max-users 200 --duration 600

Environment Variables:
    SONOTHEIA_API_KEY: API key for authentication
    SONOTHEIA_API_URL: API base URL (default: https://api.sonotheia.com)
"""

import argparse
import os
import random
import subprocess
import time

from locust import HttpUser, TaskSet, between, events, task

# Test constants
API_KEY = os.getenv("SONOTHEIA_API_KEY", "mock_api_key")
API_URL = os.getenv("SONOTHEIA_API_URL", "https://api.sonotheia.com")
SAMPLE_RATE_HZ = 16000  # Standard sample rate for audio
TEST_AUDIO_DURATION_SEC = 5.0  # Default test audio duration
SILENCE_THRESHOLD_DB = 100  # Threshold for silence detection
NUM_TEST_ENROLLMENTS = 100  # Number of reusable enrollment IDs for testing


class TestAudioGenerator:
    """Generate test audio files for load testing."""

    @staticmethod
    def create_test_audio(duration_seconds: float = 5.0) -> bytes:
        """Create in-memory test audio data.

        Returns:
            bytes: WAV file data
        """
        # For load testing, we'll create a minimal valid WAV file
        # In production, use real audio samples
        sample_rate = 16000
        num_samples = int(sample_rate * duration_seconds)

        # WAV header
        wav_header = bytearray()
        # RIFF header
        wav_header.extend(b"RIFF")
        wav_header.extend((36 + num_samples * 2).to_bytes(4, "little"))
        wav_header.extend(b"WAVE")

        # fmt chunk
        wav_header.extend(b"fmt ")
        wav_header.extend((16).to_bytes(4, "little"))  # Chunk size
        wav_header.extend((1).to_bytes(2, "little"))  # PCM format
        wav_header.extend((1).to_bytes(2, "little"))  # Mono
        wav_header.extend(sample_rate.to_bytes(4, "little"))
        wav_header.extend((sample_rate * 2).to_bytes(4, "little"))  # Byte rate
        wav_header.extend((2).to_bytes(2, "little"))  # Block align
        wav_header.extend((16).to_bytes(2, "little"))  # Bits per sample

        # data chunk
        wav_header.extend(b"data")
        wav_header.extend((num_samples * 2).to_bytes(4, "little"))

        # Generate silent audio data
        audio_data = bytes([0] * (num_samples * 2))

        return bytes(wav_header) + audio_data


class SonotheiaTaskSet(TaskSet):
    """Task set for Sonotheia API load testing."""

    def on_start(self):
        """Initialize test data."""
        self.audio_generator = TestAudioGenerator()
        self.enrollment_ids = [
            f"test-enrollment-{i}" for i in range(NUM_TEST_ENROLLMENTS)
        ]  # Reuse enrollment IDs
        self.session_counter = 0

    @task(3)
    def detect_deepfake(self):
        """Test deepfake detection endpoint."""
        audio_data = self.audio_generator.create_test_audio(duration_seconds=5.0)

        files = {"audio": ("test_audio.wav", audio_data, "audio/wav")}

        headers = {"Authorization": f"Bearer {API_KEY}"}

        metadata = {
            "session_id": f"load-test-{self.session_counter}",
            "test": "load_test",
        }

        with self.client.post(
            "/v1/voice/deepfake",
            files=files,
            data={"metadata": str(metadata)},
            headers=headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "score" in data and "label" in data:
                    response.success()
                else:
                    response.failure("Missing expected fields in response")
            else:
                response.failure(f"Got status code {response.status_code}")

        self.session_counter += 1

    @task(2)
    def verify_mfa(self):
        """Test MFA verification endpoint."""
        audio_data = self.audio_generator.create_test_audio(duration_seconds=6.0)

        files = {"audio": ("test_audio.wav", audio_data, "audio/wav")}

        headers = {"Authorization": f"Bearer {API_KEY}"}

        enrollment_id = random.choice(self.enrollment_ids)

        with self.client.post(
            "/v1/mfa/voice/verify",
            files=files,
            data={"enrollment_id": enrollment_id},
            headers=headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "verified" in data and "confidence" in data:
                    response.success()
                else:
                    response.failure("Missing expected fields in response")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def submit_sar(self):
        """Test SAR submission endpoint."""
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "session_id": f"load-test-{self.session_counter}",
            "decision": random.choice(["allow", "deny", "review"]),
            "reason": "Load test SAR submission",
            "metadata": {"test": "load_test", "timestamp": time.time()},
        }

        with self.client.post(
            "/v1/reports/sar", json=payload, headers=headers, catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "status" in data and "case_id" in data:
                    response.success()
                else:
                    response.failure("Missing expected fields in response")
            else:
                response.failure(f"Got status code {response.status_code}")


class SonotheiaUser(HttpUser):
    """Locust user class for Sonotheia API load testing."""

    tasks = [SonotheiaTaskSet]
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client.verify = True  # Verify SSL certificates


# Custom load test scenarios


class LoadTestScenario:
    """Custom load test scenarios."""

    @staticmethod
    def sustained_load(
        base_url: str, users: int = 50, duration: int = 300, spawn_rate: int = 5
    ):
        """Run sustained load test.

        Args:
            base_url: API base URL
            users: Number of concurrent users
            duration: Test duration in seconds
            spawn_rate: Users to spawn per second
        """
        print("Running sustained load test:")
        print(f"  Users: {users}")
        print(f"  Duration: {duration}s")
        print(f"  Spawn rate: {spawn_rate} users/sec")

        result = subprocess.run(
            [
                "locust",
                "-f",
                __file__,
                f"--host={base_url}",
                "--users",
                str(users),
                "--spawn-rate",
                str(spawn_rate),
                "--run-time",
                f"{duration}s",
                "--headless",
            ],
            check=True,
        )
        return result.returncode

    @staticmethod
    def spike_test(base_url: str, max_users: int = 100, duration: int = 60):
        """Run spike test (sudden increase in load).

        Args:
            base_url: API base URL
            max_users: Maximum number of users
            duration: Test duration in seconds
        """
        print("Running spike test:")
        print(f"  Max users: {max_users}")
        print(f"  Duration: {duration}s")

        # Spawn all users at once
        result = subprocess.run(
            [
                "locust",
                "-f",
                __file__,
                f"--host={base_url}",
                "--users",
                str(max_users),
                "--spawn-rate",
                str(max_users),
                "--run-time",
                f"{duration}s",
                "--headless",
            ],
            check=True,
        )
        return result.returncode

    @staticmethod
    def stress_test(base_url: str, max_users: int = 200, duration: int = 600):
        """Run stress test (gradually increasing load).

        Args:
            base_url: API base URL
            max_users: Maximum number of users
            duration: Test duration in seconds
        """
        print("Running stress test:")
        print(f"  Max users: {max_users}")
        print(f"  Duration: {duration}s")

        # Gradual ramp-up
        spawn_rate = max(1, max_users // 60)  # Reach max in ~1 minute
        result = subprocess.run(
            [
                "locust",
                "-f",
                __file__,
                f"--host={base_url}",
                "--users",
                str(max_users),
                "--spawn-rate",
                str(spawn_rate),
                "--run-time",
                f"{duration}s",
                "--headless",
            ],
            check=True,
        )
        return result.returncode


# Event handlers for custom metrics


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print(f"Starting load test against {environment.host}")
    print(f"API Key configured: {'Yes' if API_KEY else 'No'}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    stats = environment.stats

    print("\n" + "=" * 80)
    print("LOAD TEST SUMMARY")
    print("=" * 80)

    # Overall statistics
    print(f"\nTotal requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(
        f"Failure rate: {stats.total.num_failures / max(stats.total.num_requests, 1) * 100:.2f}%"
    )

    print("\nResponse times (ms):")
    print(f"  Min: {stats.total.min_response_time:.2f}")
    print(f"  Max: {stats.total.max_response_time:.2f}")
    print(f"  Average: {stats.total.avg_response_time:.2f}")
    print(f"  Median: {stats.total.median_response_time:.2f}")

    # Percentiles
    if stats.total.num_requests > 0:
        print("\nPercentiles:")
        print(f"  50th: {stats.total.get_response_time_percentile(0.5):.2f} ms")
        print(f"  75th: {stats.total.get_response_time_percentile(0.75):.2f} ms")
        print(f"  90th: {stats.total.get_response_time_percentile(0.90):.2f} ms")
        print(f"  95th: {stats.total.get_response_time_percentile(0.95):.2f} ms")
        print(f"  99th: {stats.total.get_response_time_percentile(0.99):.2f} ms")

    print(f"\nRequests per second: {stats.total.total_rps:.2f}")

    # Individual endpoint statistics
    print("\n" + "-" * 80)
    print("ENDPOINT STATISTICS")
    print("-" * 80)

    for entry in stats.entries.values():
        if entry.num_requests > 0:
            print(f"\n{entry.method} {entry.name}")
            print(f"  Requests: {entry.num_requests}")
            print(f"  Failures: {entry.num_failures}")
            print(f"  Avg response time: {entry.avg_response_time:.2f} ms")
            print(f"  RPS: {entry.total_rps:.2f}")


def main():
    """Main entry point for custom load test scenarios."""
    parser = argparse.ArgumentParser(description="Sonotheia API Load Testing")

    parser.add_argument(
        "--scenario",
        choices=["sustained", "spike", "stress"],
        default="sustained",
        help="Load test scenario",
    )
    parser.add_argument(
        "--users", type=int, default=50, help="Number of concurrent users"
    )
    parser.add_argument(
        "--max-users", type=int, default=200, help="Maximum users (for stress test)"
    )
    parser.add_argument(
        "--duration", type=int, default=300, help="Test duration in seconds"
    )
    parser.add_argument(
        "--base-url",
        default=API_URL,
        help="API base URL (default: from SONOTHEIA_API_URL)",
    )

    args = parser.parse_args()

    # Validate API key
    if not API_KEY or API_KEY == "mock_api_key":
        print(
            "WARNING: No API key configured. Set SONOTHEIA_API_KEY environment variable."
        )
        print("Continuing with mock key (may fail against real API)...")

    # Run scenario
    scenario = LoadTestScenario()

    if args.scenario == "sustained":
        scenario.sustained_load(args.base_url, args.users, args.duration)
    elif args.scenario == "spike":
        scenario.spike_test(args.base_url, args.max_users, args.duration)
    elif args.scenario == "stress":
        scenario.stress_test(args.base_url, args.max_users, args.duration)


if __name__ == "__main__":
    # Check if running as a Locust file
    import sys

    if "locust" not in sys.argv[0]:
        main()
