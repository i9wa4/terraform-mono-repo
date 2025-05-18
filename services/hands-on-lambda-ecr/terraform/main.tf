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

resource "aws_iam_role" "terraform_hands_on_lambda_ecr" {
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

resource "aws_iam_role_policy_attachment" "github_actions_oidc_role_admin_attachment" {
  role       = aws_iam_role.terraform_hands_on_lambda_ecr.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess" # TODO: Replace with a more specific policy for production use.
}
