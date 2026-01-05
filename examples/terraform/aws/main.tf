# Terraform configuration for Sonotheia API integration on AWS

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Optional: Configure remote state storage
  # backend "s3" {
  #   bucket = "my-terraform-state-bucket"
  #   key    = "sonotheia-example/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Purpose     = "Sonotheia API Integration"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Local variables
locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name

  # Resource naming
  name_prefix = "${var.project_name}-${var.environment}"

  # Lambda function names
  webhook_handler_name  = "${local.name_prefix}-webhook-handler"
  audio_processor_name  = "${local.name_prefix}-audio-processor"

  # Common tags
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
