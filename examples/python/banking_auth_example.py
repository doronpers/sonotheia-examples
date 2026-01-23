"""Banking wire transfer authentication example using Sonotheia API."""

import os
import sys
from typing import Any, Dict

# Add current directory to path so we can import client
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from client import SonotheiaClient  # noqa: E402


class WireTransferAuthenticator:
    """Wire transfer authentication handler."""

    def __init__(self, client: SonotheiaClient):
        self.client = client

    def authenticate_transfer(
        self, transfer_data: Dict[str, Any], audio_path: str
    ) -> Dict[str, Any]:
        """
        Authenticate wire transfer request.

        Args:
            transfer_data: Dict with transfer details
            audio_path: Path to voice sample file

        Returns:
            Authentication result
        """
        # Context includes transaction details AND device info
        context = {
            "amount_usd": transfer_data.get("amount", 0.0),
            "destination_country": transfer_data.get("destination_country", "US"),
            "is_new_beneficiary": transfer_data.get("is_new_beneficiary", False),
            "channel": "online_banking",
            "device_info": {
                "device_id": transfer_data.get("device_id"),
                "ip_address": transfer_data.get("ip_address"),
            },
        }

        # Perform authentication
        result = self.client.verify_mfa(
            audio_path=audio_path,
            transaction_id=transfer_data["transaction_id"],
            customer_id=transfer_data["customer_id"],
            context=context,
        )

        return result

    def process_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process authentication result."""
        decision = result.get("decision", "DECLINE")

        if decision == "APPROVE":
            return {
                "action": "execute",
                "message": "Transfer approved",
                "risk_score": result.get("risk_score"),
            }
        elif decision == "STEP_UP":
            return {
                "action": "step_up",
                "message": "Additional authentication required",
                "required_factors": result.get("required_factors", []),
            }
        else:  # DECLINE or MANUAL_REVIEW
            return {
                "action": "decline",
                "message": "Transfer declined",
                "reason": result.get("reason", "Authentication failed"),
            }


def main():
    """Run banking auth example."""
    # Initialize client (assumes local API or env vars set)
    client = SonotheiaClient()
    authenticator = WireTransferAuthenticator(client)

    # Demo Data
    transfer_data = {
        "transaction_id": "TXN_BANK_001",
        "customer_id": "CUST_998877",
        "amount": 75000.00,
        "destination_country": "US",
        "is_new_beneficiary": True,
        "device_id": "device_pixel_6",
        "ip_address": "192.168.1.105",
    }

    audio_file = "test_audio/auth_sample.wav"

    if not os.path.exists(audio_file):
        print(f"Sample audio not found at {audio_file}. Skipping execution.")
        return

    print(f"Processing transfer {transfer_data['transaction_id']}...")
    try:
        auth_result = authenticator.authenticate_transfer(transfer_data, audio_file)
        action = authenticator.process_result(auth_result)

        print("\n--- Result ---")
        print(f"Action: {action['action'].upper()}")
        print(f"Message: {action['message']}")

        if action["action"] == "decline":
            # Example: specific logic for high risk declines might trigger SAR
            print(f"Reason: {action.get('reason')}")

    except Exception as e:
        print(f"Error processing transfer: {e}")


if __name__ == "__main__":
    main()
