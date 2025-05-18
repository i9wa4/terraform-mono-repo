output "github_actions_role_arn" {
  description = "ARN of the IAM role for GitHub Actions."
  value       = aws_iam_role.github_actions_oidc_role.arn
}

output "aws_account_id" {
  description = "The AWS account ID."
  value       = var.aws_account_id
}

output "aws_region" {
  description = "The AWS region for the deployment."
  value       = var.aws_region
}
