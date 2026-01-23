"""Simple API client example for Sonotheia."""


import base64

import requests


class SimpleSonotheiaClient:
    """Minimal API client for Sonotheia."""

    def __init__(self, base_url="http://localhost:8000", api_key=None):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Accept": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
            self.headers["X-API-Key"] = api_key

    def detect(self, audio_file_path):
        """Detect deepfake using /api/detect endpoint (multipart/form-data)."""
        url = f"{self.base_url}/api/detect"

        with open(audio_file_path, "rb") as f:
            files = {"file": f}
            # requests handles multipart boundary and content-type automatically
            response = requests.post(url, files=files, headers=self.headers)

        response.raise_for_status()
        return response.json()

    def authenticate(self, transaction_id, customer_id, audio_file_path, context=None):
        """Authenticate using /api/authenticate endpoint (JSON payload)."""
        url = f"{self.base_url}/api/authenticate"
        context = context or {}

        # Base64 encode audio
        with open(audio_file_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "voice_sample": audio_b64,
            # Map context fields to top-level request parameters
            "amount_usd": context.get("amount", 0.0),
            "destination_country": context.get("country", "US"),
            "device_info": context.get("device_info", {}),
        }

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()


# Usage Example
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python simple_api_client.py <path_to_audio>")
        sys.exit(1)

    audio_path = sys.argv[1]

    client = SimpleSonotheiaClient()

    print(f"Detecting deepfake in {audio_path}...")
    try:
        # Detection
        result = client.detect(audio_path)
        print(f"Detection Score: {result.get('detection_score')}")
        print(f"Is Spoof: {result.get('is_spoof')}")

    except Exception as e:
        print(f"Error: {e}")
