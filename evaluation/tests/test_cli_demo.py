"""
Tests for CLI demo mode.
"""

from typer.testing import CliRunner

from audio_trust_harness.cli import app

runner = CliRunner()


def test_cli_demo_mode(tmp_path):
    """Test that the --demo flag runs correctly."""

    # We need to monkeypatch the script execution or ensure it runs in a temp dir if possible.
    # The actual demo generation script writes to examples/test-audio.
    # For this test, we accept that it writes to the repo path (idempotent),
    # but we want output to go to tmp_path.

    output_audit = tmp_path / "demo_audit.jsonl"

    # Run in demo mode
    # Note: This will actually trigger the subprocess call to generating scripts.
    # In a pure unit test we might mock subprocess, but for robustness testing
    # we want to ensure the integration works.
    # However, generating audio takes time.

    result = runner.invoke(app, ["run", "--demo", "--out", str(output_audit)])

    assert result.exit_code == 0
    assert "Starting run" in result.stdout
    assert "Demo mode: Using generated file" in result.stdout
    assert output_audit.exists()

    # Verify we can summarize it
    output_summary = tmp_path / "demo_summary.json"
    result_sum = runner.invoke(
        app,
        [
            "summary",
            "--audit",
            str(output_audit),
            "--out",
            str(output_summary),
            "--print-summary",
        ],
    )

    assert result_sum.exit_code == 0
    assert output_summary.exists()
    assert "Deferral Summary" in result_sum.stdout
