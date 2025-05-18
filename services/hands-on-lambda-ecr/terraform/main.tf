resource "aws_iam_role" "github_actions_oidc_role" {
  name = var.github_actions_role_name
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Federated = "arn:aws:iam::${var.aws_account_id}:oidc-provider/${var.github_oidc_provider_url}"
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
  tags = var.common_tags
}

resource "aws_iam_role_policy_attachment" "github_actions_oidc_role_admin_attachment" {
  role       = aws_iam_role.github_actions_oidc_role.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess" # Consider a more restrictive policy
}
