"""
Streaming audio processor for handling large audio files.

This example demonstrates:
- Processing long audio files by splitting into chunks
- Streaming results as they become available
- Memory-efficient processing of large files
- Progress tracking

Usage:
    SONOTHEIA_API_KEY=... python streaming_example.py path/to/long_audio.wav --chunk-duration 10
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import tempfile
from collections.abc import Generator
from typing import Any

from client_enhanced import SonotheiaClientEnhanced

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def split_audio_file(
    audio_path: str, chunk_duration_seconds: int = 10, output_dir: str | None = None
) -> Generator[tuple[int, str], None, None]:
    """
    Split audio file into chunks using ffmpeg.

    Args:
        audio_path: Path to input audio file
        chunk_duration_seconds: Duration of each chunk in seconds
        output_dir: Directory to store chunks (uses temp dir if None)

    Yields:
        Tuples of (chunk_index, chunk_path)
    """
    try:
        import subprocess
    except ImportError as err:
        raise ImportError(
            "This example requires ffmpeg. Install it with: apt-get install ffmpeg"
        ) from err

    # Create output directory
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="sonotheia_chunks_")
    else:
        os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Splitting audio file into {chunk_duration_seconds}s chunks...")

    # Get audio duration
    probe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        audio_path,
    ]

    try:
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        total_duration = float(result.stdout.strip())
        total_chunks = int(total_duration / chunk_duration_seconds) + 1
        logger.info(
            f"Audio duration: {total_duration:.2f}s, will create {total_chunks} chunks"
        )
    except subprocess.CalledProcessError as exc:
        logger.error(f"Failed to probe audio file: {exc}")
        raise

    # Split audio into chunks
    chunk_index = 0
    start_time = 0

    while start_time < total_duration:
        chunk_path = os.path.join(output_dir, f"chunk_{chunk_index:04d}.wav")

        split_cmd = [
            "ffmpeg",
            "-i",
            audio_path,
            "-ss",
            str(start_time),
            "-t",
            str(chunk_duration_seconds),
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            "-y",  # Overwrite output files
            chunk_path,
        ]

        try:
            subprocess.run(split_cmd, capture_output=True, check=True)
            yield chunk_index, chunk_path
            chunk_index += 1
            start_time += chunk_duration_seconds
        except subprocess.CalledProcessError as exc:
            logger.error(f"Failed to create chunk {chunk_index}: {exc}")
            raise


def process_streaming(
    audio_path: str,
    chunk_duration: int = 10,
    enrollment_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    Process audio file in streaming fashion.

    Args:
        audio_path: Path to audio file
        chunk_duration: Duration of each chunk in seconds
        enrollment_id: Optional enrollment ID for MFA
        session_id: Optional session ID for tracking

    Returns:
        Aggregated results from all chunks
    """
    session_id = session_id or f"stream-{os.path.basename(audio_path)}"

    with SonotheiaClientEnhanced(
        max_retries=3,
        rate_limit_rps=2.0,  # Conservative rate limit for streaming
    ) as client:
        results = {
            "session_id": session_id,
            "audio_file": audio_path,
            "chunks": [],
            "summary": {
                "total_chunks": 0,
                "avg_deepfake_score": 0.0,
                "max_deepfake_score": 0.0,
                "high_risk_chunks": 0,
            },
        }

        total_score = 0.0
        chunk_count = 0

        # Process each chunk
        for chunk_idx, chunk_path in split_audio_file(audio_path, chunk_duration):
            logger.info(f"Processing chunk {chunk_idx}...")

            chunk_result = {
                "chunk_index": chunk_idx,
                "chunk_path": chunk_path,
            }

            try:
                # Deepfake detection for chunk
                deepfake_result = client.detect_deepfake(
                    chunk_path,
                    metadata={
                        "session_id": session_id,
                        "chunk_index": chunk_idx,
                        "parent_file": audio_path,
                    },
                )
                chunk_result["deepfake"] = deepfake_result

                score = deepfake_result.get("score", 0.0)
                total_score += score
                chunk_count += 1

                # Track high-risk chunks
                if score > 0.7:
                    results["summary"]["high_risk_chunks"] += 1
                    logger.warning(
                        f"Chunk {chunk_idx} has high deepfake score: {score}"
                    )

                # Optional MFA for each chunk
                if enrollment_id:
                    mfa_result = client.verify_mfa(
                        chunk_path,
                        enrollment_id,
                        context={
                            "session_id": session_id,
                            "chunk_index": chunk_idx,
                        },
                    )
                    chunk_result["mfa"] = mfa_result

            except Exception as exc:
                logger.error(f"Failed to process chunk {chunk_idx}: {exc}")
                chunk_result["error"] = str(exc)

            results["chunks"].append(chunk_result)

            # Clean up chunk file
            try:
                os.remove(chunk_path)
            except OSError:
                pass

        # Calculate summary statistics
        if chunk_count > 0:
            results["summary"]["total_chunks"] = chunk_count
            results["summary"]["avg_deepfake_score"] = total_score / chunk_count
            results["summary"]["max_deepfake_score"] = max(
                (c.get("deepfake", {}).get("score", 0.0) for c in results["chunks"]),
                default=0.0,
            )

        # Submit SAR if high-risk chunks detected
        if results["summary"]["high_risk_chunks"] > 0:
            logger.info(
                f"Submitting SAR for {results['summary']['high_risk_chunks']} high-risk chunks"
            )
            try:
                sar_result = client.submit_sar(
                    session_id,
                    decision="review",
                    reason=f"Detected {results['summary']['high_risk_chunks']} high-risk chunks in streaming audio",
                    metadata={
                        "source": "streaming-example",
                        "avg_score": results["summary"]["avg_deepfake_score"],
                        "max_score": results["summary"]["max_deepfake_score"],
                    },
                )
                results["sar"] = sar_result
            except Exception as exc:
                logger.error(f"Failed to submit SAR: {exc}")

        return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stream and process long audio files in chunks"
    )
    parser.add_argument("audio", help="Path to audio file")
    parser.add_argument(
        "--chunk-duration",
        type=int,
        default=10,
        help="Duration of each chunk in seconds (default: 10)",
    )
    parser.add_argument("--enrollment-id", help="Enrollment ID for MFA verification")
    parser.add_argument("--session-id", help="Session identifier")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not os.path.exists(args.audio):
        logger.error(f"Audio file not found: {args.audio}")
        sys.exit(1)

    try:
        results = process_streaming(
            args.audio,
            chunk_duration=args.chunk_duration,
            enrollment_id=args.enrollment_id,
            session_id=args.session_id,
        )

        print("\n=== Streaming Processing Results ===")
        print(json.dumps(results, indent=2))

        # Exit with error if high-risk chunks detected
        if results["summary"]["high_risk_chunks"] > 0:
            sys.exit(1)

    except Exception as exc:
        logger.error(f"Streaming processing failed: {exc}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
