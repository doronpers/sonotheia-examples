# Input variables for Sonotheia AWS infrastructure

# Required variables
variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name (used in resource naming)"
  type        = string
  default     = "sonotheia-example"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "sonotheia_api_key" {
  description = "Sonotheia API key for authentication"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.sonotheia_api_key) > 0
    error_message = "Sonotheia API key must not be empty."
  }
}

# Optional variables
variable "environment" {
  description = "Environment name (dev/staging/prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "sonotheia_api_url" {
  description = "Sonotheia API base URL"
  type        = string
  default     = "https://api.sonotheia.com"
}

# Lambda configuration
variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512

  validation {
    condition     = var.lambda_memory_size >= 128 && var.lambda_memory_size <= 10240
    error_message = "Lambda memory size must be between 128 and 10240 MB."
  }
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30

  validation {
    condition     = var.lambda_timeout >= 3 && var.lambda_timeout <= 900
    error_message = "Lambda timeout must be between 3 and 900 seconds."
  }
}

variable "lambda_runtime" {
  description = "Lambda function runtime"
  type        = string
  default     = "python3.11"
}

# Feature flags
variable "enable_api_gateway" {
  description = "Enable API Gateway for webhook endpoints"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring and alarms"
  type        = bool
  default     = true
}

variable "enable_vpc" {
  description = "Deploy Lambda functions in VPC"
  type        = bool
  default     = false
}

# S3 configuration
variable "s3_audio_retention_days" {
  description = "Number of days to retain audio files in S3"
  type        = number
  default     = 30

  validation {
    condition     = var.s3_audio_retention_days >= 1
    error_message = "S3 retention days must be at least 1."
  }
}

variable "enable_s3_versioning" {
  description = "Enable S3 bucket versioning"
  type        = bool
  default     = false
}

# DynamoDB configuration
variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"

  validation {
    condition     = contains(["PROVISIONED", "PAY_PER_REQUEST"], var.dynamodb_billing_mode)
    error_message = "DynamoDB billing mode must be PROVISIONED or PAY_PER_REQUEST."
  }
}

variable "dynamodb_read_capacity" {
  description = "DynamoDB read capacity units (only for PROVISIONED mode)"
  type        = number
  default     = 5
}

variable "dynamodb_write_capacity" {
  description = "DynamoDB write capacity units (only for PROVISIONED mode)"
  type        = number
  default     = 5
}

variable "dynamodb_ttl_enabled" {
  description = "Enable DynamoDB TTL for automatic record expiration"
  type        = bool
  default     = true
}

variable "dynamodb_ttl_days" {
  description = "Number of days before DynamoDB records expire"
  type        = number
  default     = 90
}

# Monitoring configuration
variable "alarm_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  default     = ""
}

variable "enable_xray_tracing" {
  description = "Enable AWS X-Ray tracing for Lambda functions"
  type        = bool
  default     = false
}

# Webhook configuration
variable "webhook_secret" {
  description = "Secret for webhook signature verification (optional, generated if not provided)"
  type        = string
  default     = ""
  sensitive   = true
}

# Tags
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
