# Output values for Sonotheia AWS infrastructure

# API Gateway outputs
output "webhook_url" {
  description = "Webhook endpoint URL for Sonotheia API callbacks"
  value       = var.enable_api_gateway ? aws_api_gateway_stage.main[0].invoke_url : "API Gateway not enabled"
}

output "api_gateway_id" {
  description = "API Gateway REST API ID"
  value       = var.enable_api_gateway ? aws_api_gateway_rest_api.main[0].id : null
}

# Lambda outputs
output "webhook_handler_function_name" {
  description = "Webhook handler Lambda function name"
  value       = aws_lambda_function.webhook_handler.function_name
}

output "webhook_handler_arn" {
  description = "Webhook handler Lambda function ARN"
  value       = aws_lambda_function.webhook_handler.arn
}

output "audio_processor_function_name" {
  description = "Audio processor Lambda function name"
  value       = aws_lambda_function.audio_processor.function_name
}

output "audio_processor_arn" {
  description = "Audio processor Lambda function ARN"
  value       = aws_lambda_function.audio_processor.arn
}

# S3 outputs
output "s3_bucket_name" {
  description = "S3 bucket name for audio file storage"
  value       = aws_s3_bucket.audio.id
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.audio.arn
}

# DynamoDB outputs
output "dynamodb_table_name" {
  description = "DynamoDB table name for session tracking"
  value       = aws_dynamodb_table.sessions.name
}

output "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  value       = aws_dynamodb_table.sessions.arn
}

# IAM outputs
output "lambda_execution_role_arn" {
  description = "Lambda execution role ARN"
  value       = aws_iam_role.lambda_execution.arn
}

# CloudWatch outputs
output "webhook_handler_log_group" {
  description = "CloudWatch log group for webhook handler"
  value       = aws_cloudwatch_log_group.webhook_handler.name
}

output "audio_processor_log_group" {
  description = "CloudWatch log group for audio processor"
  value       = aws_cloudwatch_log_group.audio_processor.name
}

# Secrets Manager outputs
output "api_key_secret_arn" {
  description = "Secrets Manager ARN for Sonotheia API key"
  value       = aws_secretsmanager_secret.sonotheia_api_key.arn
}

# Monitoring outputs
output "sns_topic_arn" {
  description = "SNS topic ARN for alarm notifications"
  value       = var.enable_monitoring ? aws_sns_topic.alarms[0].arn : null
}

# Deployment information
output "deployment_info" {
  description = "Deployment information summary"
  value = {
    project_name = var.project_name
    environment  = var.environment
    region       = var.aws_region
    deployed_at  = timestamp()
  }
}

# Usage instructions
output "usage_instructions" {
  description = "Instructions for using the deployed infrastructure"
  value = <<-EOT
    
    === Sonotheia AWS Infrastructure Deployed ===
    
    Webhook URL: ${var.enable_api_gateway ? aws_api_gateway_stage.main[0].invoke_url : "API Gateway not enabled"}
    
    S3 Bucket: ${aws_s3_bucket.audio.id}
    DynamoDB Table: ${aws_dynamodb_table.sessions.name}
    
    To upload audio files:
      aws s3 cp audio.wav s3://${aws_s3_bucket.audio.id}/incoming/
    
    To view webhook logs:
      aws logs tail ${aws_cloudwatch_log_group.webhook_handler.name} --follow
    
    To query DynamoDB:
      aws dynamodb scan --table-name ${aws_dynamodb_table.sessions.name}
    
    To register this webhook with Sonotheia:
      curl -X POST https://api.sonotheia.com/v1/webhooks \
        -H "Authorization: Bearer YOUR_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"url": "${var.enable_api_gateway ? "${aws_api_gateway_stage.main[0].invoke_url}/webhook" : "API_GATEWAY_NOT_ENABLED"}", "events": ["deepfake.completed", "mfa.completed", "sar.submitted"]}'
  EOT
}
