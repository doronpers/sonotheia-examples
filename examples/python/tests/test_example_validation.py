"""
Example Validation Tests

These tests validate that example scripts work correctly and produce expected outputs.
They can be run as part of CI/CD to ensure examples remain functional.

Run tests:
    pytest tests/test_example_validation.py -v

Run specific validation:
    pytest tests/test_example_validation.py::TestGoldenPathValidation -v
"""

import json
import os
import subprocess
import sys
import tempfile

import pytest
import requests


def create_test_audio_file(duration_seconds: float = 5.0) -> str:
    """Create a test WAV file using ffmpeg."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_file.close()

    # Generate silent audio
    command = [
        "ffmpeg",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=16000:cl=mono",
        "-t",
        str(duration_seconds),
        "-y",
        temp_file.name,
    ]

    try:
        subprocess.run(command, capture_output=True, check=True)
        return temp_file.name
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("ffmpeg not available - cannot create test audio files")
        return ""  # Never reached, but satisfies type checker


@pytest.fixture(scope="module")
def mock_server():
    """Start mock API server for validation tests."""
    import subprocess
    import time

    # Check if Flask is available (required for mock server)
    try:
        import flask  # noqa: F401
    except ImportError:
        pytest.skip("Flask not available - mock server requires Flask")

    MOCK_API_PORT = 8916  # Different port to avoid conflicts with other tests
    MOCK_API_URL = f"http://localhost:{MOCK_API_PORT}"

    # Determine path to mock_api_server.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    mock_server_path = os.path.join(current_dir, "..", "mock_api_server.py")

    # Start server in subprocess
    process = subprocess.Popen(
        [sys.executable, mock_server_path, "--port", str(MOCK_API_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(mock_server_path),  # Run from correct directory
    )

    # Wait for server to start
    max_retries = 30
    started = False
    for _i in range(max_retries):
        try:
            response = requests.get(f"{MOCK_API_URL}/health", timeout=1)
            if response.status_code == 200:
                started = True
                break
        except requests.exceptions.RequestException:
            time.sleep(0.5)

    if not started:
        # Get error output before killing
        try:
            stdout, stderr = process.communicate(timeout=1)
            error_msg = (
                f"Mock server failed to start. stdout: {stdout.decode()}, stderr: {stderr.decode()}"
            )
        except subprocess.TimeoutExpired:
            error_msg = "Mock server failed to start (timeout getting error output)"
        process.kill()
        pytest.skip(f"Mock server failed to start: {error_msg}")

    yield {"api_url": MOCK_API_URL, "process": process}

    # Cleanup
    try:
        process.terminate()
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture
def test_audio():
    """Create a test audio file."""
    audio_path = create_test_audio_file(duration_seconds=5.0)
    yield audio_path
    try:
        os.unlink(audio_path)
    except OSError:
        pass


class TestGoldenPathValidation:
    """Validate Golden Path demo script works correctly."""

    def test_golden_path_demo_runs_with_mock(self, mock_server, test_audio):
        """Test that golden_path_demo.py runs successfully in mock mode."""
        # Get path to golden_path_demo.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        demo_script = os.path.join(current_dir, "..", "golden_path_demo.py")

        # Run the script
        env = os.environ.copy()
        env["SONOTHEIA_API_URL"] = mock_server["api_url"]
        env["SONOTHEIA_API_KEY"] = "mock_key"

        result = subprocess.run(
            [sys.executable, demo_script, test_audio, "--mock", "--json"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

        # Check exit code
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        # Parse JSON output
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {result.stdout}\nError: {e}")

        # Validate output contract
        assert "session_id" in output
        assert "timestamp" in output
        assert "inputs" in output
        assert "results" in output
        assert "decision" in output
        assert "diagnostics" in output

        # Validate inputs
        assert "audio_filename" in output["inputs"]
        assert "audio_seconds" in output["inputs"]
        assert "samplerate_hz" in output["inputs"]

        # Validate results structure
        assert "deepfake" in output["results"]
        assert "score" in output["results"]["deepfake"]
        assert 0.0 <= output["results"]["deepfake"]["score"] <= 1.0

        # Validate decision structure
        assert "route" in output["decision"]
        assert "reasons" in output["decision"]
        assert isinstance(output["decision"]["reasons"], list)

        # Validate route is one of expected values
        valid_routes = [
            "ALLOW",
            "REQUIRE_STEP_UP",
            "REQUIRE_CALLBACK",
            "ESCALATE_TO_HUMAN",
            "BLOCK",
        ]
        assert output["decision"]["route"] in valid_routes

    def test_golden_path_demo_with_mfa(self, mock_server, test_audio):
        """Test Golden Path demo with MFA verification."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        demo_script = os.path.join(current_dir, "..", "golden_path_demo.py")

        env = os.environ.copy()
        env["SONOTHEIA_API_URL"] = mock_server["api_url"]
        env["SONOTHEIA_API_KEY"] = "mock_key"

        result = subprocess.run(
            [
                sys.executable,
                demo_script,
                test_audio,
                "--mock",
                "--enrollment-id",
                "test-enrollment-123",
                "--json",
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"

        output = json.loads(result.stdout)

        # Should have MFA results
        assert "mfa" in output["results"]
        assert "verified" in output["results"]["mfa"]
        assert isinstance(output["results"]["mfa"]["verified"], bool)

    def test_golden_path_demo_output_contract(self, mock_server, test_audio):
        """Validate Golden Path output matches standardized contract."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        demo_script = os.path.join(current_dir, "..", "golden_path_demo.py")

        env = os.environ.copy()
        env["SONOTHEIA_API_URL"] = mock_server["api_url"]
        env["SONOTHEIA_API_KEY"] = "mock_key"

        result = subprocess.run(
            [sys.executable, demo_script, test_audio, "--mock", "--json"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)

        # Validate all required top-level fields
        required_fields = [
            "session_id",
            "timestamp",
            "inputs",
            "results",
            "decision",
            "diagnostics",
        ]
        for field in required_fields:
            assert field in output, f"Missing required field: {field}"

        # Validate timestamp format (ISO-8601)
        timestamp = output["timestamp"]
        assert timestamp.endswith("Z") or "+" in timestamp or "-" in timestamp

        # Validate no secrets in output
        output_str = json.dumps(output)
        assert "api_key" not in output_str.lower()
        assert "secret" not in output_str.lower()
        assert "password" not in output_str.lower()

        # Validate no numpy types (should be native Python types)
        # This is checked by ensuring JSON serialization works
        json.dumps(output)  # Should not raise TypeError

    def test_golden_path_demo_handles_errors(self, mock_server):
        """Test that Golden Path demo handles errors gracefully."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        demo_script = os.path.join(current_dir, "..", "golden_path_demo.py")

        env = os.environ.copy()
        env["SONOTHEIA_API_URL"] = mock_server["api_url"]
        env["SONOTHEIA_API_KEY"] = "mock_key"

        # Test with non-existent file
        result = subprocess.run(
            [sys.executable, demo_script, "nonexistent.wav", "--mock", "--json"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

        # Should fail gracefully
        assert result.returncode != 0
        # Should output error information
        assert len(result.stderr) > 0 or "error" in result.stdout.lower()


class TestClientExampleValidation:
    """Validate client example scripts work correctly."""

    def test_client_basic_usage(self, mock_server, test_audio):
        """Test that basic client usage example works."""
        # This would test if there's a basic example script
        # For now, we test the client module directly
        from client import SonotheiaClient

        client = SonotheiaClient(api_key="mock_key", api_url=mock_server["api_url"])

        result = client.detect_deepfake(test_audio)

        assert "score" in result
        assert "label" in result
        assert 0.0 <= result["score"] <= 1.0


class TestWebhookReceiverValidation:
    """Validate webhook receiver example works correctly."""

    def test_webhook_receiver_starts(self):
        """Test that webhook receiver can start without errors."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        webhook_app = os.path.join(current_dir, "..", "webhook_receiver", "app.py")

        # Try to import and validate it's a valid FastAPI app
        import importlib.util

        spec = importlib.util.spec_from_file_location("webhook_app", webhook_app)
        if spec is None:
            pytest.skip("Could not load webhook app spec")

        # Type narrowing: spec is not None here
        assert spec is not None  # Type guard for mypy
        loader = spec.loader
        if loader is None:
            pytest.skip("Could not load webhook app loader")

        # Type narrowing: loader is not None here
        assert loader is not None  # Type guard for mypy
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)

        # Check that app exists and is a FastAPI instance
        assert hasattr(module, "app")
        from fastapi import FastAPI

        assert isinstance(module.app, FastAPI)


class TestOutputContractCompliance:
    """Validate that all example outputs comply with the standardized contract."""

    def test_golden_path_output_is_json_safe(self, mock_server, test_audio):
        """Ensure output contains only JSON-safe types."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        demo_script = os.path.join(current_dir, "..", "golden_path_demo.py")

        env = os.environ.copy()
        env["SONOTHEIA_API_URL"] = mock_server["api_url"]
        env["SONOTHEIA_API_KEY"] = "mock_key"

        result = subprocess.run(
            [sys.executable, demo_script, test_audio, "--mock", "--json"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)

        # Recursively check for JSON-safe types
        def check_json_safe(obj, path=""):
            """Recursively validate object is JSON-safe."""
            if obj is None:
                return
            elif isinstance(obj, (str, int, float, bool)):
                return  # These are JSON-safe
            elif isinstance(obj, dict):
                for key, value in obj.items():
                    check_json_safe(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_json_safe(item, f"{path}[{i}]")
            else:
                # Check for numpy types or other non-JSON types
                type_name = type(obj).__name__
                if "numpy" in type_name.lower() or "ndarray" in type_name.lower():
                    pytest.fail(f"Found non-JSON type at {path}: {type_name}")

        check_json_safe(output)
