"""
Advanced audio analysis example with DSP features.

This example demonstrates:
- Extracting DSP features from audio files
- Analyzing audio quality and integrity
- Making routing decisions based on confidence scores
- Interpreting audio analysis results

Usage:
    python audio_analysis_example.py audio.wav
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AudioAnalysisClient:
    """Client for audio analysis with DSP features."""

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.sonotheia.com",
        tenant_id: str = "demo"
    ):
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        self.tenant_id = tenant_id

    def _headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-Tenant-ID": self.tenant_id,
            "Accept": "application/json",
        }

    def analyze_audio(
        self,
        audio_path: str,
        extract_features: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze audio file for deepfake detection with DSP features.

        Args:
            audio_path: Path to audio file
            extract_features: Whether to extract detailed DSP features

        Returns:
            Analysis results with anomaly score and features
        """
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Analyzing audio file: {audio_path}")

        with open(audio_file, "rb") as f:
            files = {"audio": (audio_file.name, f, "audio/wav")}
            data = {
                "extract_features": str(extract_features).lower(),
                "include_reason_codes": "true",
            }

            response = requests.post(
                f"{self.api_url}/v1/voice/deepfake",
                headers=self._headers(),
                files=files,
                data=data,
                timeout=30.0,
            )

        response.raise_for_status()
        return response.json()

    def extract_features_only(self, audio_path: str) -> Dict[str, Any]:
        """
        Extract DSP features without full analysis.

        Args:
            audio_path: Path to audio file

        Returns:
            DSP features dictionary
        """
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Extracting features from: {audio_path}")

        with open(audio_file, "rb") as f:
            files = {"audio": (audio_file.name, f, "audio/wav")}
            data = {"mode": "features_only"}

            response = requests.post(
                f"{self.api_url}/v1/voice/features",
                headers=self._headers(),
                files=files,
                data=data,
                timeout=30.0,
            )

        response.raise_for_status()
        return response.json()


def interpret_results(result: Dict[str, Any]) -> str:
    """
    Interpret analysis results and recommend action.

    Args:
        result: Analysis result from API

    Returns:
        Recommended action string
    """
    score = result.get("score", 0.0)
    confidence = result.get("confidence", 0.0)
    label = result.get("label", "unknown")

    print("\n" + "=" * 70)
    print("AUDIO ANALYSIS RESULTS")
    print("=" * 70)
    print(f"Label:          {label}")
    print(f"Deepfake Score: {score:.3f}")
    print(f"Confidence:     {confidence:.3f}")
    print()

    # Interpret risk level
    if score > 0.7:
        risk_level = "HIGH"
    elif score > 0.4:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    print(f"Risk Level:     {risk_level}")

    # Show reason codes if available
    if "reason_codes" in result:
        print("\nReason Codes:")
        for code in result["reason_codes"]:
            print(f"  - {code}")

    # Show feature contributions if available
    if "feature_contributions" in result:
        print("\nFeature Contributions:")
        for feature, contribution in result["feature_contributions"].items():
            print(f"  {feature:25s}: {contribution:.3f}")
    print()

    # Routing decision based on confidence and score
    if confidence < 0.6:
        action = "ESCALATE_TO_HUMAN"
        reason = "Low confidence - requires human review"
    elif risk_level == "HIGH":
        action = "BLOCK"
        reason = "High risk - likely synthetic audio detected"
    elif risk_level == "MEDIUM":
        action = "REQUIRE_ADDITIONAL_CONTROLS"
        reason = "Medium risk - apply callback or step-up authentication"
    else:
        action = "ALLOW"
        reason = "Low risk - appears authentic"

    print(f"RECOMMENDED ACTION: {action}")
    print(f"Reason: {reason}")
    print("=" * 70 + "\n")

    return action


def display_dsp_features(features: Dict[str, Any]):
    """
    Display DSP features in a readable format.

    Args:
        features: DSP features dictionary
    """
    print("\nDSP Features Summary:")
    print("-" * 70)

    # Basic audio properties
    if "duration_sec" in features:
        print(f"Duration:           {features['duration_sec']:.2f} seconds")
    if "sample_rate" in features:
        print(f"Sample Rate:        {features['sample_rate']} Hz")

    # Spectral features
    if "spectral_centroid" in features:
        print(f"Spectral Centroid:  {features['spectral_centroid']:.1f} Hz")
    if "spectral_rolloff" in features:
        print(f"Spectral Rolloff:   {features['spectral_rolloff']:.1f} Hz")
    if "spectral_flatness" in features:
        print(f"Spectral Flatness:  {features['spectral_flatness']:.3f}")

    # Energy distribution
    if "band_energy_ratio_low" in features:
        print(f"Low Band Energy:    {features['band_energy_ratio_low']:.3f}")
    if "band_energy_ratio_high" in features:
        print(f"High Band Energy:   {features['band_energy_ratio_high']:.3f}")

    # Signal dynamics
    if "crest_factor" in features:
        print(f"Crest Factor:       {features['crest_factor']:.2f} dB")
    if "clipping_rate" in features:
        print(f"Clipping Rate:      {features['clipping_rate']:.4f}")

    # Voice quality indicators
    if "hnr_db" in features:
        print(f"HNR:                {features['hnr_db']:.2f} dB")
    if "jitter_percent" in features:
        print(f"Jitter:             {features['jitter_percent']:.3f}%")
    if "shimmer_percent" in features:
        print(f"Shimmer:            {features['shimmer_percent']:.3f}%")

    # Advanced features
    if "phase_coherence" in features:
        print(f"Phase Coherence:    {features['phase_coherence']:.3f}")
    if "spectral_flux" in features:
        print(f"Spectral Flux:      {features['spectral_flux']:.2f}")

    # Formants
    if "formant_frequencies" in features:
        formants = ", ".join(f"{f:.0f} Hz" for f in features['formant_frequencies'][:4])
        print(f"Formants (F1-F4):   {formants}")

    print("-" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Advanced audio analysis with DSP features"
    )
    parser.add_argument("audio", help="Path to audio file")
    parser.add_argument(
        "--api-url",
        default="https://api.sonotheia.com",
        help="API base URL"
    )
    parser.add_argument(
        "--api-key",
        help="API key (or set SONOTHEIA_API_KEY env var)"
    )
    parser.add_argument(
        "--tenant-id",
        default="demo",
        help="Tenant ID (default: demo)"
    )
    parser.add_argument(
        "--features-only",
        action="store_true",
        help="Extract features only without full analysis"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get API key
    import os
    api_key = args.api_key or os.getenv("SONOTHEIA_API_KEY")
    if not api_key:
        logger.error("API key required. Set SONOTHEIA_API_KEY or use --api-key")
        sys.exit(1)

    # Create client
    client = AudioAnalysisClient(
        api_key=api_key,
        api_url=args.api_url,
        tenant_id=args.tenant_id
    )

    try:
        if args.features_only:
            # Extract features only
            features = client.extract_features_only(args.audio)
            display_dsp_features(features)

        else:
            # Full analysis with features
            result = client.analyze_audio(args.audio, extract_features=True)

            # Interpret results and get recommended action
            action = interpret_results(result)

            # Display DSP features if available
            if "dsp_features" in result:
                display_dsp_features(result["dsp_features"])

            # Save full results to JSON
            output_file = Path(args.audio).with_suffix(".json")
            with open(output_file, "w") as f:
                json.dump(result, f, indent=2)
            logger.info(f"Full results saved to: {output_file}")

    except requests.HTTPError as e:
        logger.error(f"API Error: {e.response.status_code}")
        if hasattr(e.response, 'json'):
            logger.error(f"Details: {e.response.json()}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"File Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
