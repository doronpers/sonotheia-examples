#!/usr/bin/env python3
"""
Generate test audio files for Sonotheia API testing.

This script creates various test audio files using ffmpeg for testing
different scenarios and edge cases.

Requirements:
    - ffmpeg installed and available in PATH

Usage:
    python generate_test_audio.py
    python generate_test_audio.py --output-dir /path/to/output
    python generate_test_audio.py --file-list basic  # Only basic files
"""

import argparse
import os
import subprocess
import sys
from typing import Dict, List, Tuple


class AudioFileGenerator:
    """Generate test audio files using ffmpeg."""

    def __init__(self, output_dir: str = "."):
        """Initialize generator.

        Args:
            output_dir: Directory to save generated files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available.

        Returns:
            bool: True if ffmpeg is available
        """
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def generate_file(self, filename: str, ffmpeg_args: List[str]) -> bool:
        """Generate a single audio file.

        Args:
            filename: Output filename
            ffmpeg_args: ffmpeg command arguments

        Returns:
            bool: True if successful
        """
        output_path = os.path.join(self.output_dir, filename)

        # Add -y flag to overwrite existing files
        if "-y" not in ffmpeg_args:
            ffmpeg_args.insert(0, "-y")

        # Add output path
        ffmpeg_args.append(output_path)

        # Build full command
        command = ["ffmpeg"] + ffmpeg_args

        try:
            print(f"Generating: {filename}... ", end="", flush=True)
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print("✓")
            return True
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode()[:100] if e.stderr else "Unknown error"
            print(f"✗ (Error: {error_msg})")
            return False

    def generate_basic_files(self) -> Dict[str, bool]:
        """Generate basic test files.

        Returns:
            Dict[str, bool]: Mapping of filename to success status
        """
        files = {
            "silent_5s.wav": ["-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-t", "5"],
            "silent_10s.wav": ["-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-t", "10"],
            "silent_3s.wav": ["-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-t", "3"],
            "tone_440hz_5s.wav": [
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:sample_rate=16000:duration=5",
                "-ac",
                "1",
            ],
            "tone_440hz_10s.wav": [
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:sample_rate=16000:duration=10",
                "-ac",
                "1",
            ],
        }

        results = {}
        for filename, args in files.items():
            results[filename] = self.generate_file(filename, args)

        return results

    def generate_edge_case_files(self) -> Dict[str, bool]:
        """Generate edge case test files.

        Returns:
            Dict[str, bool]: Mapping of filename to success status
        """
        files = {
            "short_1s.wav": ["-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-t", "1"],
            "long_30s.wav": ["-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-t", "30"],
            "stereo_5s.wav": ["-f", "lavfi", "-i", "anullsrc=r=16000:cl=stereo", "-t", "5"],
            "8khz_5s.wav": ["-f", "lavfi", "-i", "anullsrc=r=8000:cl=mono", "-t", "5"],
            "48khz_5s.wav": ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", "5"],
        }

        results = {}
        for filename, args in files.items():
            results[filename] = self.generate_file(filename, args)

        return results

    def generate_noise_files(self) -> Dict[str, bool]:
        """Generate noise test files.

        Returns:
            Dict[str, bool]: Mapping of filename to success status
        """
        files = {
            "white_noise_5s.wav": [
                "-f",
                "lavfi",
                "-i",
                "anoisesrc=d=5:c=white:r=16000:a=0.5",
                "-ac",
                "1",
            ],
            "pink_noise_5s.wav": [
                "-f",
                "lavfi",
                "-i",
                "anoisesrc=d=5:c=pink:r=16000:a=0.5",
                "-ac",
                "1",
            ],
        }

        results = {}
        for filename, args in files.items():
            results[filename] = self.generate_file(filename, args)

        return results

    def generate_all(self) -> Tuple[int, int]:
        """Generate all test files.

        Returns:
            Tuple[int, int]: (successful, total) file counts
        """
        all_results = {}

        print("\n=== Generating Basic Files ===")
        all_results.update(self.generate_basic_files())

        print("\n=== Generating Edge Case Files ===")
        all_results.update(self.generate_edge_case_files())

        print("\n=== Generating Noise Files ===")
        all_results.update(self.generate_noise_files())

        successful = sum(1 for success in all_results.values() if success)
        total = len(all_results)

        return successful, total


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate test audio files for Sonotheia API testing"
    )

    parser.add_argument(
        "--output-dir",
        default=".",
        help="Output directory for generated files (default: current directory)",
    )

    parser.add_argument(
        "--file-list",
        choices=["all", "basic", "edge", "noise"],
        default="all",
        help="Which files to generate (default: all)",
    )

    args = parser.parse_args()

    # Initialize generator
    generator = AudioFileGenerator(args.output_dir)

    # Check ffmpeg
    print("Checking for ffmpeg...")
    if not generator.check_ffmpeg():
        print("ERROR: ffmpeg not found in PATH")
        print("\nPlease install ffmpeg:")
        print("  Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("  macOS:         brew install ffmpeg")
        print("  Windows:       choco install ffmpeg")
        sys.exit(1)

    print("✓ ffmpeg found\n")

    # Generate files based on selection
    results = {}

    if args.file_list == "all":
        successful, total = generator.generate_all()
    elif args.file_list == "basic":
        print("\n=== Generating Basic Files ===")
        results = generator.generate_basic_files()
        successful = sum(1 for s in results.values() if s)
        total = len(results)
    elif args.file_list == "edge":
        print("\n=== Generating Edge Case Files ===")
        results = generator.generate_edge_case_files()
        successful = sum(1 for s in results.values() if s)
        total = len(results)
    elif args.file_list == "noise":
        print("\n=== Generating Noise Files ===")
        results = generator.generate_noise_files()
        successful = sum(1 for s in results.values() if s)
        total = len(results)

    # Summary
    print("\n" + "=" * 50)
    print(f"SUMMARY: {successful}/{total} files generated successfully")
    print("=" * 50)

    if successful < total:
        print("\nSome files failed to generate. Check errors above.")
        sys.exit(1)
    else:
        print(f"\nAll test files generated in: {os.path.abspath(args.output_dir)}")
        sys.exit(0)


if __name__ == "__main__":
    main()
