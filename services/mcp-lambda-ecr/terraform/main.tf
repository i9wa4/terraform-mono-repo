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
