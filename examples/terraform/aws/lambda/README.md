# Lambda Functions

This directory contains Lambda function code for Sonotheia API integration.

## Functions

### webhook_handler.py

Handles incoming webhook events from Sonotheia API.

**Trigger:** API Gateway POST /webhook
**Purpose:** Receive and process webhook events (deepfake.completed, mfa.completed, sar.submitted)

### audio_processor.py

Processes audio files uploaded to S3.

**Trigger:** S3 object creation in `incoming/` folder
**Purpose:** Send audio files to Sonotheia API and store results

## Building Lambda Packages

### Prerequisites

```bash
pip install boto3 requests
```

### Build Script

Run the build script to create deployment packages:

```bash
./build_lambda.sh
```

Or build manually:

```bash
# Webhook handler
cd lambda
mkdir -p package
pip install boto3 requests -t package/
cp webhook_handler.py package/
cd package
zip -r ../webhook_handler.zip .
cd ..

# Audio processor
mkdir -p package
pip install boto3 requests -t package/
cp audio_processor.py package/
cd package
zip -r ../audio_processor.zip .
cd ..
```

### Deploy with Terraform

After building the zip files, deploy with Terraform:

```bash
cd ..
terraform init
terraform apply
```

## Environment Variables

Both functions use these environment variables (set by Terraform):

- `DYNAMODB_TABLE`: DynamoDB table name
- `S3_BUCKET`: S3 bucket name
- `API_KEY_SECRET_ARN`: Secrets Manager ARN for API key
- `SONOTHEIA_API_URL`: Sonotheia API base URL
- `ENVIRONMENT`: Environment name (dev/staging/prod)

## Testing Locally

### Test webhook handler

```python
import json
from webhook_handler import lambda_handler

# Mock API Gateway event
event = {
    'body': json.dumps({
        'event_type': 'deepfake.completed',
        'event_id': 'evt_test123',
        'data': {
            'session_id': 'sess_test',
            'score': 0.82,
            'label': 'likely_synthetic'
        }
    }),
    'headers': {}
}

result = lambda_handler(event, None)
print(result)
```

### Test audio processor

```python
from audio_processor import lambda_handler

# Mock S3 event
event = {
    'Records': [{
        's3': {
            'bucket': {'name': 'test-bucket'},
            'object': {'key': 'incoming/test.wav'}
        }
    }]
}

result = lambda_handler(event, None)
print(result)
```

## Customization

Both functions include TODO comments for custom logic:

- **webhook_handler.py**: Add notification logic, external system integration
- **audio_processor.py**: Add custom audio preprocessing, result handling

## Dependencies

- `boto3`: AWS SDK (included in Lambda runtime)
- `requests`: HTTP library (must be packaged)

## Related Documentation

- [Terraform Configuration](../README.md)
- [Webhook Schemas](../../../../docs/WEBHOOK_SCHEMAS.md)
- [Best Practices](../../../../docs/BEST_PRACTICES.md)
