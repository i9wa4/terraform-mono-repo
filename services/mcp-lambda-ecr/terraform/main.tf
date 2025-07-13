provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role" "terraform_mcp_lambda_ecr" {
  name = var.project_name
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${var.github_oidc_provider_url}"
        },
        Action = "sts:AssumeRoleWithWebIdentity",
        Condition = {
          StringLike = {
            "${var.github_oidc_provider_url}:sub" = "repo:${var.github_repository}:*",
            "${var.github_oidc_provider_url}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })
}

# TODO: Replace with a more specific policy for production use.
#   ref: https://github.com/JamesWoolfenden/pike
resource "aws_iam_role_policy_attachment" "github_actions_oidc_role_admin_attachment" {
  role       = aws_iam_role.terraform_mcp_lambda_ecr.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_ecr_repository" "app_ecr_repos" {
  for_each = toset(var.lambda_app_names)

  name                 = "${var.project_name}-${var.environment}-${each.key}"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true  # Allow deletion even when images exist

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
    AppName     = each.key
    ManagedBy   = "Terraform"
  }
}

resource "aws_secretsmanager_secret" "this" {
  name        = "${var.project_name}/${var.environment}/common"
  description = "Secret for ${var.project_name}. Repository: ${var.github_repository}."
}

resource "aws_secretsmanager_secret_version" "this" {
  secret_id = aws_secretsmanager_secret.this.id
  secret_string = jsonencode({
    X_API_KEY      = "dummy"
    GEMINI_API_KEY = "dummy"
  })

  lifecycle {
    ignore_changes = [
      secret_string,
    ]
  }
}

locals {
  network_secret_name = "${var.project_name}/${var.environment}/network-config"
}

resource "aws_secretsmanager_secret" "network_config" {
  name        = local.network_secret_name
  description = "VPC configuration for the ${var.project_name} project in ${var.environment} environment."
}

resource "aws_secretsmanager_secret_version" "network_config" {
  secret_id = aws_secretsmanager_secret.network_config.id
  secret_string = jsonencode({
    vpc_id                 = aws_vpc.this.id
    private_subnet_ids     = aws_subnet.private[*].id
    lambda_security_group_id = aws_security_group.lambda.id
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}
