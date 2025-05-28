provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      AppName     = local.app_name
      ManagedBy   = "Terraform"
    }
  }
}

locals {
  app_name             = basename(abspath(path.module))
  lambda_function_name = "${var.project_name}-${var.environment}-${local.app_name}"
  secret_name          = "${var.project_name}/${var.environment}/${local.app_name}"
}

data "aws_caller_identity" "current" {}

data "aws_ecr_repository" "this" {
  name = local.lambda_function_name
}

resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${local.lambda_function_name}"
  retention_in_days = var.log_retention_days != null ? var.log_retention_days : 7
}

resource "aws_secretsmanager_secret" "this" {
  name        = local.secret_name
  description = "Secret for ${local.lambda_function_name}. Repository: ${var.github_repository}. WARNING: Managed by Terraform."
}

resource "aws_secretsmanager_secret_version" "this" {
  secret_id = aws_secretsmanager_secret.this.id
  secret_string = jsonencode({
    FUNCTION_URL = aws_lambda_function_url.this.function_url
    FUNCTION_ARN = aws_lambda_function.this.arn
  })
}

# --------------------
# Resources for Lambda
#
resource "aws_iam_policy" "lambda_exec_policy" {
  name        = "${local.lambda_function_name}-exec-policy"
  description = "IAM policy for Lambda ${local.lambda_function_name} to pull from ECR and write to CloudWatch Logs"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "ECRToken",
        Effect = "Allow",
        Action = [
          "ecr:GetAuthorizationToken"
        ],
        Resource = [
          "*" #tfsec:ignore:AWS099
        ]
      },
      {
        Sid    = "ECRImagePull",
        Effect = "Allow",
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer"
        ],
        Resource = [
          data.aws_ecr_repository.this.arn
        ]
      },
      {
        Sid    = "CloudWatchLogsWrite",
        Effect = "Allow",
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = [
          "${aws_cloudwatch_log_group.lambda_log_group.arn}:*"
        ]
      }
    ]
  })
}

resource "aws_iam_role" "lambda_exec_role" {
  name = "${local.lambda_function_name}-exec-role"

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
}

resource "aws_iam_role_policy_attachment" "lambda_exec_policy_attachment" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_exec_policy.arn
}

resource "aws_lambda_function" "this" {
  function_name = local.lambda_function_name
  role          = aws_iam_role.lambda_exec_role.arn
  package_type  = "Image"
  image_uri     = var.image_uri
  architectures = [
    var.lambda_architecture
  ]

  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout

  depends_on = [
    aws_cloudwatch_log_group.lambda_log_group,
    aws_iam_role_policy_attachment.lambda_exec_policy_attachment
  ]
}

resource "aws_lambda_function_url" "this" {
  function_name      = aws_lambda_function.this.function_name
  authorization_type = "AWS_IAM"

  # 必要に応じてCORS設定
  # cors {
  #   allow_origins = ["*"] # 呼び出し元に応じて適切に設定
  #   allow_methods = ["POST", "GET"]
  # }
}
