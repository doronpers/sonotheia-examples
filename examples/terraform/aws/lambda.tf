# Lambda functions configuration

# Webhook handler Lambda function
resource "aws_lambda_function" "webhook_handler" {
  filename      = "${path.module}/lambda/webhook_handler.zip"
  function_name = local.webhook_handler_name
  role          = aws_iam_role.lambda_execution.arn
  handler       = "webhook_handler.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  source_code_hash = filebase64sha256("${path.module}/lambda/webhook_handler.zip")

  environment {
    variables = {
      DYNAMODB_TABLE       = aws_dynamodb_table.sessions.name
      S3_BUCKET            = aws_s3_bucket.audio.id
      API_KEY_SECRET_ARN   = aws_secretsmanager_secret.sonotheia_api_key.arn
      SONOTHEIA_API_URL    = var.sonotheia_api_url
      ENVIRONMENT          = var.environment
    }
  }

  tracing_config {
    mode = var.enable_xray_tracing ? "Active" : "PassThrough"
  }

  tags = merge(
    local.common_tags,
    {
      Name = local.webhook_handler_name
    }
  )
}

# CloudWatch log group for webhook handler
resource "aws_cloudwatch_log_group" "webhook_handler" {
  name              = "/aws/lambda/${local.webhook_handler_name}"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = local.common_tags
}

# Audio processor Lambda function
resource "aws_lambda_function" "audio_processor" {
  filename      = "${path.module}/lambda/audio_processor.zip"
  function_name = local.audio_processor_name
  role          = aws_iam_role.lambda_execution.arn
  handler       = "audio_processor.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  source_code_hash = filebase64sha256("${path.module}/lambda/audio_processor.zip")

  environment {
    variables = {
      DYNAMODB_TABLE       = aws_dynamodb_table.sessions.name
      S3_BUCKET            = aws_s3_bucket.audio.id
      API_KEY_SECRET_ARN   = aws_secretsmanager_secret.sonotheia_api_key.arn
      SONOTHEIA_API_URL    = var.sonotheia_api_url
      ENVIRONMENT          = var.environment
    }
  }

  tracing_config {
    mode = var.enable_xray_tracing ? "Active" : "PassThrough"
  }

  tags = merge(
    local.common_tags,
    {
      Name = local.audio_processor_name
    }
  )
}

# CloudWatch log group for audio processor
resource "aws_cloudwatch_log_group" "audio_processor" {
  name              = "/aws/lambda/${local.audio_processor_name}"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = local.common_tags
}

# Lambda permission for S3 to invoke audio processor
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.audio_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.audio.arn
}

# Lambda permission for API Gateway to invoke webhook handler
resource "aws_lambda_permission" "allow_apigateway" {
  count = var.enable_api_gateway ? 1 : 0

  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.webhook_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main[0].execution_arn}/*/*/*"
}
