# API Gateway configuration for webhook endpoints

# REST API
resource "aws_api_gateway_rest_api" "main" {
  count = var.enable_api_gateway ? 1 : 0

  name        = "${local.name_prefix}-api"
  description = "Sonotheia webhook API for ${var.environment}"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = local.common_tags
}

# /webhook resource
resource "aws_api_gateway_resource" "webhook" {
  count = var.enable_api_gateway ? 1 : 0

  rest_api_id = aws_api_gateway_rest_api.main[0].id
  parent_id   = aws_api_gateway_rest_api.main[0].root_resource_id
  path_part   = "webhook"
}

# POST /webhook method
resource "aws_api_gateway_method" "webhook_post" {
  count = var.enable_api_gateway ? 1 : 0

  rest_api_id   = aws_api_gateway_rest_api.main[0].id
  resource_id   = aws_api_gateway_resource.webhook[0].id
  http_method   = "POST"
  authorization = "NONE"
}

# Lambda integration for POST /webhook
resource "aws_api_gateway_integration" "webhook_post" {
  count = var.enable_api_gateway ? 1 : 0

  rest_api_id             = aws_api_gateway_rest_api.main[0].id
  resource_id             = aws_api_gateway_resource.webhook[0].id
  http_method             = aws_api_gateway_method.webhook_post[0].http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.webhook_handler.invoke_arn
}

# /health resource for health checks
resource "aws_api_gateway_resource" "health" {
  count = var.enable_api_gateway ? 1 : 0

  rest_api_id = aws_api_gateway_rest_api.main[0].id
  parent_id   = aws_api_gateway_rest_api.main[0].root_resource_id
  path_part   = "health"
}

# GET /health method
resource "aws_api_gateway_method" "health_get" {
  count = var.enable_api_gateway ? 1 : 0

  rest_api_id   = aws_api_gateway_rest_api.main[0].id
  resource_id   = aws_api_gateway_resource.health[0].id
  http_method   = "GET"
  authorization = "NONE"
}

# Mock integration for GET /health
resource "aws_api_gateway_integration" "health_get" {
  count = var.enable_api_gateway ? 1 : 0

  rest_api_id = aws_api_gateway_rest_api.main[0].id
  resource_id = aws_api_gateway_resource.health[0].id
  http_method = aws_api_gateway_method.health_get[0].http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

# Mock integration response
resource "aws_api_gateway_integration_response" "health_get" {
  count = var.enable_api_gateway ? 1 : 0

  rest_api_id = aws_api_gateway_rest_api.main[0].id
  resource_id = aws_api_gateway_resource.health[0].id
  http_method = aws_api_gateway_method.health_get[0].http_method
  status_code = "200"

  response_templates = {
    "application/json" = jsonencode({
      status    = "healthy"
      timestamp = "$context.requestTime"
    })
  }

  depends_on = [aws_api_gateway_integration.health_get]
}

# Method response for GET /health
resource "aws_api_gateway_method_response" "health_get" {
  count = var.enable_api_gateway ? 1 : 0

  rest_api_id = aws_api_gateway_rest_api.main[0].id
  resource_id = aws_api_gateway_resource.health[0].id
  http_method = aws_api_gateway_method.health_get[0].http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }
}

# Deployment
resource "aws_api_gateway_deployment" "main" {
  count = var.enable_api_gateway ? 1 : 0

  rest_api_id = aws_api_gateway_rest_api.main[0].id

  depends_on = [
    aws_api_gateway_integration.webhook_post,
    aws_api_gateway_integration.health_get
  ]

  lifecycle {
    create_before_destroy = true
  }
}

# Stage
resource "aws_api_gateway_stage" "main" {
  count = var.enable_api_gateway ? 1 : 0

  deployment_id = aws_api_gateway_deployment.main[0].id
  rest_api_id   = aws_api_gateway_rest_api.main[0].id
  stage_name    = var.environment

  xray_tracing_enabled = var.enable_xray_tracing

  tags = local.common_tags
}

# Usage plan (for rate limiting)
resource "aws_api_gateway_usage_plan" "main" {
  count = var.enable_api_gateway ? 1 : 0

  name = "${local.name_prefix}-usage-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.main[0].id
    stage  = aws_api_gateway_stage.main[0].stage_name
  }

  throttle_settings {
    burst_limit = 100
    rate_limit  = 50
  }

  quota_settings {
    limit  = 10000
    period = "DAY"
  }
}
