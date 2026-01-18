"""
Webhook handler Lambda function for Sonotheia API.

This function receives webhook events from the Sonotheia API and processes them.
It validates signatures, stores events in DynamoDB, and triggers downstream actions.

Environment Variables:
    DYNAMODB_TABLE: DynamoDB table name for session storage
    S3_BUCKET: S3 bucket name for audio file storage
    API_KEY_SECRET_ARN: Secrets Manager ARN for Sonotheia API key
    SONOTHEIA_API_URL: Sonotheia API base URL
    ENVIRONMENT: Environment name (dev/staging/prod)
"""

import hashlib
import hmac
import json
import os
from datetime import datetime

import boto3

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
secretsmanager = boto3.client("secretsmanager")


# Validate and load environment variables
def validate_environment():
    """Validate all required environment variables are set."""
    required_vars = [
        "DYNAMODB_TABLE",
        "S3_BUCKET",
        "API_KEY_SECRET_ARN",
        "SONOTHEIA_API_URL",
        "ENVIRONMENT",
    ]
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


validate_environment()

# Environment variables
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
S3_BUCKET = os.environ["S3_BUCKET"]
API_KEY_SECRET_ARN = os.environ["API_KEY_SECRET_ARN"]
SONOTHEIA_API_URL = os.environ["SONOTHEIA_API_URL"]
ENVIRONMENT = os.environ["ENVIRONMENT"]
WEBHOOK_SECRET_ARN = os.environ.get("WEBHOOK_SECRET_ARN")


def lambda_handler(event, context):
    """
    Lambda handler for webhook events.

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        dict: Response with statusCode and body
    """
    try:
        # Parse request
        body = event.get("body", "{}")
        headers = event.get("headers", {})

        # Validate signature (required in production)
        signature = headers.get("X-Sonotheia-Signature", "")
        if ENVIRONMENT == "prod":
            if not signature:
                return error_response(401, "Missing webhook signature")
            webhook_secret = get_webhook_secret()
            if not webhook_secret:
                print("ERROR: Webhook secret not configured for production environment")
                return error_response(500, "Server configuration error")
            if not verify_signature(body, signature, webhook_secret):
                return error_response(401, "Invalid webhook signature")

        # Parse webhook event
        webhook_event = json.loads(body)
        event_type = webhook_event.get("event_type")
        event_id = webhook_event.get("event_id")
        event_data = webhook_event.get("data", {})

        print(f"Processing webhook event: {event_type} (ID: {event_id})")

        # Store event in DynamoDB
        store_event(webhook_event)

        # Process event based on type
        if event_type == "deepfake.completed":
            process_deepfake_event(event_data)
        elif event_type == "mfa.completed":
            process_mfa_event(event_data)
        elif event_type == "sar.submitted":
            process_sar_event(event_data)
        else:
            print(f"Unknown event type: {event_type}")

        # Return success response
        return {"statusCode": 200, "body": json.dumps({"status": "success", "event_id": event_id})}

    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"status": "error", "message": str(e)})}


def store_event(webhook_event):
    """Store webhook event in DynamoDB."""
    table = dynamodb.Table(DYNAMODB_TABLE)

    session_id = webhook_event.get("data", {}).get("session_id", "unknown")
    timestamp = int(datetime.utcnow().timestamp())

    # Calculate TTL (90 days from now)
    ttl = timestamp + (90 * 24 * 60 * 60)

    item = {
        "session_id": session_id,
        "timestamp": timestamp,
        "event_type": webhook_event.get("event_type"),
        "event_id": webhook_event.get("event_id"),
        "data": webhook_event.get("data"),
        "ttl": ttl,
    }

    table.put_item(Item=item)
    print(f"Stored event in DynamoDB: {session_id}")


def process_deepfake_event(data):
    """Process deepfake detection event."""
    session_id = data.get("session_id")
    score = data.get("score")
    label = data.get("label")

    print(f"Deepfake event: {session_id}, score={score}, label={label}")

    # Send high-risk alerts
    if score and score > 0.8:
        print(f"HIGH RISK: Deepfake score {score} for session {session_id}")
        # TODO: Send SNS notification, trigger alert workflow

    # TODO: Implement additional custom processing logic
    # - Send notifications
    # - Update external systems
    # - Trigger additional workflows


def process_mfa_event(data):
    """Process MFA verification event."""
    session_id = data.get("session_id")
    verified = data.get("verified")
    confidence = data.get("confidence")
    enrollment_id = data.get("enrollment_id")

    print(f"MFA event: {session_id}, verified={verified}, confidence={confidence}")

    # Log authentication result
    if not verified:
        print(f"AUTHENTICATION FAILED: {enrollment_id} (session: {session_id})")
        # TODO: Log failed authentication attempt, trigger security review

    # TODO: Implement additional custom processing logic
    # - Update user session
    # - Grant/deny access
    # - Send verification result to frontend


def process_sar_event(data):
    """Process SAR submission event."""
    case_id = data.get("case_id")
    session_id = data.get("session_id")
    status = data.get("status")

    print(f"SAR event: {case_id}, session={session_id}, status={status}")

    # Log SAR submission for compliance
    print(f"COMPLIANCE: SAR case {case_id} submitted with status {status}")

    # TODO: Implement additional custom processing logic
    # - Send SNS notification to compliance team
    # - Update case management system
    # - Archive evidence to S3
    # - Create audit log entry


def get_webhook_secret():
    """Retrieve webhook secret from Secrets Manager."""
    if not WEBHOOK_SECRET_ARN:
        return None

    try:
        response = secretsmanager.get_secret_value(SecretId=WEBHOOK_SECRET_ARN)
        secret_string = response.get("SecretString")
        if secret_string:
            secret_data = json.loads(secret_string)
            return secret_data.get("webhook_secret")
        return None
    except Exception as e:
        print(f"Error retrieving webhook secret: {str(e)}")
        return None


def verify_signature(payload, signature, secret):
    """Verify webhook signature."""
    expected = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()

    received = signature.replace("sha256=", "")
    return hmac.compare_digest(expected, received)


def error_response(status_code, message):
    """Return error response."""
    return {"statusCode": status_code, "body": json.dumps({"status": "error", "message": message})}
