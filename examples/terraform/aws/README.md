# Terraform AWS Infrastructure for Sonotheia Examples

This directory contains Terraform configurations for deploying Sonotheia API integration examples on AWS.

## Overview

The Terraform configuration provisions:
- **Lambda Functions**: For serverless API integration
- **API Gateway**: REST API endpoint for webhook handling
- **S3 Bucket**: For audio file storage and processing
- **DynamoDB Table**: For session tracking and results storage
- **IAM Roles**: Appropriate permissions for Lambda execution
- **CloudWatch Logs**: For monitoring and debugging
- **Secrets Manager**: Secure API key storage

## Architecture

```
┌─────────────────┐
│  API Gateway    │ ← Webhook endpoint
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Lambda Function │ ← Process webhook events
└────────┬────────┘
         │
    ┌────┴─────┬──────────┬────────────┐
    ↓          ↓          ↓            ↓
┌───────┐ ┌─────────┐ ┌────────┐ ┌──────────┐
│   S3  │ │DynamoDB │ │Secrets │ │CloudWatch│
│Bucket │ │  Table  │ │Manager │ │   Logs   │
└───────┘ └─────────┘ └────────┘ └──────────┘
```

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Terraform** installed (version 1.0+)
3. **AWS CLI** configured with credentials
4. **Sonotheia API Key**

### Install Terraform

```bash
# macOS
brew install terraform

# Linux
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Windows (using Chocolatey)
choco install terraform

# Verify installation
terraform version
```

### Configure AWS CLI

```bash
aws configure
# Enter: AWS Access Key ID, Secret Access Key, Region, Output format
```

## Quick Start

### 1. Set Variables

Create a `terraform.tfvars` file:

```hcl
# terraform.tfvars
aws_region          = "us-east-1"
project_name        = "sonotheia-example"
environment         = "dev"
sonotheia_api_key   = "your-api-key-here"  # Or use Secrets Manager
sonotheia_api_url   = "https://api.sonotheia.com"

# Optional
enable_api_gateway  = true
enable_monitoring   = true
lambda_memory_size  = 512
lambda_timeout      = 30
```

**Security Note:** Do NOT commit `terraform.tfvars` with API keys to version control!

### 2. Build Lambda Packages

**Important:** Build Lambda deployment packages before running Terraform:

```bash
cd lambda
./build_lambda.sh
cd ..
```

This creates `webhook_handler.zip` and `audio_processor.zip` files needed for deployment.

### 3. Initialize Terraform

```bash
terraform init
```

### 4. Preview Changes

```bash
terraform plan
```

### 5. Deploy Infrastructure

```bash
terraform apply
```

Review the plan and type `yes` to confirm.

### 6. Get Outputs

```bash
terraform output
```

Example output:
```
webhook_url = "https://abc123.execute-api.us-east-1.amazonaws.com/prod/webhook"
s3_bucket_name = "sonotheia-example-audio-dev"
dynamodb_table_name = "sonotheia-example-sessions-dev"
```

## Configuration Options

### Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `aws_region` | AWS region for deployment | `us-east-1` |
| `project_name` | Project name (used in resource naming) | `sonotheia-example` |
| `sonotheia_api_key` | Sonotheia API key | (required) |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `environment` | Environment name (dev/staging/prod) | `dev` |
| `sonotheia_api_url` | Sonotheia API URL | `https://api.sonotheia.com` |
| `lambda_memory_size` | Lambda memory in MB | `512` |
| `lambda_timeout` | Lambda timeout in seconds | `30` |
| `enable_api_gateway` | Enable API Gateway for webhooks | `true` |
| `enable_monitoring` | Enable CloudWatch monitoring | `true` |
| `s3_audio_retention_days` | S3 audio file retention period | `30` |

## Usage Examples

### Deploy to Production

```bash
# Create production.tfvars
cat > production.tfvars <<EOF
aws_region = "us-west-2"
project_name = "sonotheia-prod"
environment = "prod"
lambda_memory_size = 1024
lambda_timeout = 60
enable_monitoring = true
EOF

# Deploy
terraform apply -var-file=production.tfvars
```

### Deploy Multiple Environments

```bash
# Development
terraform workspace new dev
terraform apply -var-file=dev.tfvars

# Staging
terraform workspace new staging
terraform apply -var-file=staging.tfvars

# Production
terraform workspace new prod
terraform apply -var-file=prod.tfvars
```

### Update Configuration

```bash
# Modify variables in terraform.tfvars
# Apply changes
terraform apply
```

### Destroy Infrastructure

```bash
# Preview destruction
terraform plan -destroy

# Destroy all resources
terraform destroy
```

## Lambda Functions

### Webhook Handler

**File:** `lambda/webhook_handler.py`

Handles incoming webhook events from Sonotheia API:
- Validates webhook signatures
- Processes deepfake, MFA, and SAR events
- Stores results in DynamoDB
- Triggers downstream processing

### Audio Processor

**File:** `lambda/audio_processor.py`

Processes audio files from S3:
- Retrieves audio from S3
- Sends to Sonotheia API
- Stores results
- Triggers notifications

## API Gateway Endpoints

### POST /webhook

Receives webhook events from Sonotheia API.

**Request:**
```json
{
  "event_type": "deepfake.completed",
  "data": {
    "session_id": "sess_123",
    "score": 0.82,
    "label": "likely_synthetic"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "event_id": "evt_456"
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-05T12:34:56Z"
}
```

## Storage

### S3 Bucket

**Structure:**
```
s3://sonotheia-example-audio-dev/
├── incoming/          # Uploaded audio files
├── processed/         # Processed audio files
└── archives/          # Archived files (after retention period)
```

**Lifecycle Policy:**
- Move to IA (Infrequent Access) after 30 days
- Archive to Glacier after 90 days
- Delete after 365 days (configurable)

### DynamoDB Table

**Schema:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `session_id` (PK) | String | Session identifier |
| `timestamp` (SK) | Number | Unix timestamp |
| `event_type` | String | Event type |
| `data` | Map | Event data |
| `status` | String | Processing status |
| `ttl` | Number | Time-to-live (auto-delete) |

## Monitoring

### CloudWatch Metrics

Available metrics:
- Lambda invocations
- Lambda errors
- Lambda duration
- API Gateway requests
- API Gateway latency
- DynamoDB read/write capacity

### CloudWatch Alarms

Configured alarms:
- Lambda error rate > 5%
- Lambda duration > 25s
- API Gateway 5xx errors > 10
- DynamoDB throttling

### CloudWatch Logs

Log groups:
- `/aws/lambda/sonotheia-webhook-handler-dev`
- `/aws/lambda/sonotheia-audio-processor-dev`
- `/aws/apigateway/sonotheia-example-dev`

View logs:
```bash
# Stream webhook handler logs
aws logs tail /aws/lambda/sonotheia-webhook-handler-dev --follow

# Query logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/sonotheia-webhook-handler-dev \
  --filter-pattern "ERROR"
```

## Security

### API Key Storage

**Option 1: Secrets Manager (Recommended)**

```bash
# Store API key in Secrets Manager
aws secretsmanager create-secret \
  --name sonotheia-api-key-dev \
  --secret-string "your-api-key"

# Terraform will retrieve automatically
```

**Option 2: Environment Variable**

```bash
export TF_VAR_sonotheia_api_key="your-api-key"
terraform apply
```

### IAM Permissions

Lambda functions have minimal required permissions:
- S3: Read/Write to audio bucket only
- DynamoDB: Read/Write to sessions table only
- Secrets Manager: Read API key only
- CloudWatch Logs: Write logs only

### Network Security

- API Gateway: HTTPS only
- Lambda: VPC optional (can be enabled for private APIs)
- S3: Block public access
- DynamoDB: Encrypted at rest

## Cost Estimation

Estimated monthly costs for **1000 requests/day**:

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 30K invocations, 512MB, 5s avg | $0.85 |
| API Gateway | 30K requests | $0.11 |
| S3 | 1GB storage, 30K requests | $0.05 |
| DynamoDB | On-demand, 30K reads/writes | $1.50 |
| CloudWatch Logs | 1GB logs | $0.50 |
| **Total** | | **~$3/month** |

**Note:** Costs scale with usage. Use AWS Cost Calculator for precise estimates.

## Troubleshooting

### Common Issues

#### Issue: Terraform Init Fails

```bash
# Clear cache and reinitialize
rm -rf .terraform
terraform init
```

#### Issue: Lambda Deployment Fails

```bash
# Package Lambda function manually
cd lambda
zip -r function.zip webhook_handler.py
aws lambda update-function-code \
  --function-name sonotheia-webhook-handler-dev \
  --zip-file fileb://function.zip
```

#### Issue: API Gateway 403 Errors

- Check API Gateway resource policy
- Verify IAM role permissions
- Check CloudWatch logs for details

#### Issue: DynamoDB Throttling

- Increase DynamoDB provisioned capacity
- Or switch to on-demand billing mode

### Debug Terraform

```bash
# Enable debug logging
export TF_LOG=DEBUG
terraform apply

# Validate configuration
terraform validate

# Format configuration
terraform fmt
```

## Cleanup

### Remove All Resources

```bash
# Destroy infrastructure
terraform destroy

# Delete S3 bucket (if not empty)
aws s3 rm s3://sonotheia-example-audio-dev --recursive
aws s3 rb s3://sonotheia-example-audio-dev

# Delete CloudWatch logs
aws logs delete-log-group --log-group-name /aws/lambda/sonotheia-webhook-handler-dev
```

## Migration Guide

### From Manual Deployment

1. Document existing resources
2. Import resources into Terraform:
   ```bash
   terraform import aws_lambda_function.webhook <function-name>
   terraform import aws_s3_bucket.audio <bucket-name>
   ```
3. Verify state matches reality
4. Apply Terraform configuration

### Between AWS Regions

1. Update `aws_region` in `terraform.tfvars`
2. Run `terraform plan` to preview changes
3. Create new infrastructure: `terraform apply`
4. Migrate data (S3 sync, DynamoDB export/import)
5. Update DNS/endpoints
6. Destroy old infrastructure

## Advanced Topics

### CI/CD Integration

```yaml
# .github/workflows/terraform.yml
name: Terraform Deploy
on:
  push:
    branches: [main]
    paths: ['examples/terraform/aws/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: hashicorp/setup-terraform@v2
      - name: Terraform Init
        run: terraform init
      - name: Terraform Apply
        run: terraform apply -auto-approve
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          TF_VAR_sonotheia_api_key: ${{ secrets.SONOTHEIA_API_KEY }}
```

### Multi-Region Deployment

```hcl
# Deploy to multiple regions
module "us_east" {
  source = "./modules/sonotheia"
  aws_region = "us-east-1"
}

module "eu_west" {
  source = "./modules/sonotheia"
  aws_region = "eu-west-1"
}
```

## Related Documentation

- [Webhook Schemas](../../../docs/WEBHOOK_SCHEMAS.md)
- [Best Practices](../../../docs/BEST_PRACTICES.md)
- [Python Examples](../../python/README.md)
- [Kubernetes Deployment](../../kubernetes/README.md)

## Support

For issues with:
- **Terraform configuration**: Open an issue in this repository
- **AWS services**: Check AWS documentation or AWS Support
- **Sonotheia API**: Contact your integration engineer

---

**Last Updated**: January 5, 2026  
**Terraform Version**: 1.6+  
**AWS Provider Version**: 5.0+
