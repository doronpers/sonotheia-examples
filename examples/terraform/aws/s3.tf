# S3 bucket for audio file storage

resource "aws_s3_bucket" "audio" {
  bucket = "${local.name_prefix}-audio"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-audio"
      Purpose = "Audio file storage for Sonotheia processing"
    }
  )
}

# Block public access
resource "aws_s3_bucket_public_access_block" "audio" {
  bucket = aws_s3_bucket.audio.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable versioning (optional)
resource "aws_s3_bucket_versioning" "audio" {
  count  = var.enable_s3_versioning ? 1 : 0
  bucket = aws_s3_bucket.audio.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "audio" {
  bucket = aws_s3_bucket.audio.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Lifecycle policy
resource "aws_s3_bucket_lifecycle_configuration" "audio" {
  bucket = aws_s3_bucket.audio.id

  rule {
    id     = "archive-old-audio"
    status = "Enabled"

    # Move to Infrequent Access after retention period
    transition {
      days          = var.s3_audio_retention_days
      storage_class = "STANDARD_IA"
    }

    # Move to Glacier after 90 days
    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    # Delete after 1 year
    expiration {
      days = 365
    }
  }

  rule {
    id     = "cleanup-incomplete-uploads"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# S3 bucket notification to trigger Lambda on upload
resource "aws_s3_bucket_notification" "audio" {
  bucket = aws_s3_bucket.audio.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.audio_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "incoming/"
    filter_suffix       = ".wav"
  }

  depends_on = [aws_lambda_permission.allow_s3]
}
