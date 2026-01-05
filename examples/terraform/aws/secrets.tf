# Secrets Manager for storing Sonotheia API key

resource "aws_secretsmanager_secret" "sonotheia_api_key" {
  name        = "${local.name_prefix}-sonotheia-api-key"
  description = "Sonotheia API key for ${var.environment} environment"

  recovery_window_in_days = var.environment == "prod" ? 30 : 0

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-sonotheia-api-key"
    }
  )
}

resource "aws_secretsmanager_secret_version" "sonotheia_api_key" {
  secret_id     = aws_secretsmanager_secret.sonotheia_api_key.id
  secret_string = var.sonotheia_api_key
}

# Webhook secret (optional)
resource "random_password" "webhook_secret" {
  length  = 32
  special = true
}

resource "aws_secretsmanager_secret" "webhook_secret" {
  name        = "${local.name_prefix}-webhook-secret"
  description = "Webhook signature secret for ${var.environment} environment"

  recovery_window_in_days = var.environment == "prod" ? 30 : 0

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-webhook-secret"
    }
  )
}

resource "aws_secretsmanager_secret_version" "webhook_secret" {
  secret_id     = aws_secretsmanager_secret.webhook_secret.id
  secret_string = var.webhook_secret != "" ? var.webhook_secret : random_password.webhook_secret.result
}
