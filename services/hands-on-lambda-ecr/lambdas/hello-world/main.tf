provider "aws" {
  region = var.aws_region
  default_tags {
    tags = merge(
      {
        Project     = var.project_name
        Environment = var.environment
        LambdaName  = var.lambda_name_suffix
      },
      var.common_tags
    )
  }
}

locals {
  effective_function_name = "${var.project_name}-${var.environment}-${var.lambda_name_suffix}"
}

data "aws_caller_identity" "current" {}

resource "aws_ecr_repository" "lambda_ecr_repo" {
  name                 = local.effective_function_name
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
  # Tags are handled by the provider's default_tags
}

resource "aws_iam_role" "lambda_exec_role" {
  name = "${local.effective_function_name}-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  # Tags are handled by the provider's default_tags
}

resource "aws_iam_policy" "lambda_exec_policy" {
  name        = "${local.effective_function_name}-exec-policy"
  description = "IAM policy for Lambda ${local.effective_function_name} to pull from ECR and write to CloudWatch Logs"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup"
        ],
        Effect   = "Allow",
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${local.effective_function_name}:*"
      },
      {
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Effect   = "Allow",
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${local.effective_function_name}:log-stream:*"
      },
      {
        Action = [
          "ecr:GetAuthorizationToken"
        ],
        Effect   = "Allow",
        Resource = "*" #tfsec:ignore:AWS099
      },
      {
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer"
        ],
        Effect   = "Allow",
        Resource = aws_ecr_repository.lambda_ecr_repo.arn
      }
    ]
  })
  # Tags are handled by the provider's default_tags for the policy resource itself, if applicable by AWS.
  # The policy content itself does not have tags.
}

resource "aws_iam_role_policy_attachment" "lambda_exec_policy_attachment" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_exec_policy.arn
}

resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${local.effective_function_name}"
  retention_in_days = var.log_retention_days != null ? var.log_retention_days : 7
  # Tags are handled by the provider's default_tags
}

resource "aws_lambda_function" "this" {
  function_name = local.effective_function_name
  role          = aws_iam_role.lambda_exec_role.arn
  package_type  = "Image"
  image_uri     = var.image_uri

  memory_size = var.lambda_memory_size != null ? var.lambda_memory_size : 256
  timeout     = var.lambda_timeout != null ? var.lambda_timeout : 30

  # Tags are handled by the provider's default_tags

  depends_on = [aws_cloudwatch_log_group.lambda_log_group]
}
