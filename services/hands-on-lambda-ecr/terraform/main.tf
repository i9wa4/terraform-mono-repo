resource "aws_ecr_repository" "app_ecr_repo" {
  name                 = var.ecr_repository_name
  image_tag_mutability = "IMMUTABLE" # 本番環境では IMMUTABLE を推奨

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# 現在のAWSアカウントIDとリージョンを取得するためのデータソース
data "aws_caller_identity" "current" {}
# リージョンは var.aws_region を使用

# Lambda実行ロール
resource "aws_iam_role" "lambda_exec_role" {
  name = "${var.lambda_function_name}-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement =
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# LambdaがECRからプルし、CloudWatch Logsに書き込むためのIAMポリシー
resource "aws_iam_policy" "lambda_exec_policy" {
  name        = "${var.lambda_function_name}-exec-policy"
  description = "IAM policy for Lambda to pull from ECR and write to CloudWatch Logs"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup"
        ],
        Effect   = "Allow",
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.lambda_function_name}:*"
      },
      {
        Action =,
        Effect   = "Allow",
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.lambda_function_name}:log-stream:*"
      },
      {
        Action =,
        Effect   = "Allow",
        Resource = "*" # GetAuthorizationTokenにはワイルドカードリソースが必要
      },
      {
        Action =,
        Effect   = "Allow",
        Resource = aws_ecr_repository.app_ecr_repo.arn
      }
    ]
  })
}

# ポリシーをロールにアタッチ
resource "aws_iam_role_policy_attachment" "lambda_exec_policy_attachment" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_exec_policy.arn
}

resource "aws_lambda_function" "hello_world_lambda" {
  function_name = var.lambda_function_name
  role          = aws_iam_role.lambda_exec_role.arn
  package_type  = "Image"
  image_uri     = var.ecr_image_uri # CI/CDによって提供される

  # オプション: メモリとタイムアウトの設定
  memory_size = 256 # MB
  timeout     = 30  # 秒

  # オプション: 環境変数
  # environment {
  #   variables = {
  #     GREETING = "Hola"
  #   }
  # }

  # コンテナイメージの場合、image_configでDockerfileのCMDやENTRYPOINTを上書き可能
  # DockerfileのCMDが正しく設定されていれば、通常は不要
  # image_config {
  #   command = ["app.handler"]
  # }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }

  # Lambda関数がCloudWatch Log Groupに依存することを明示
  # これにより、TerraformはLog Groupを先に作成しようとします
  depends_on = [aws_cloudwatch_log_group.lambda_log_group]
}

# Lambda関数のためのCloudWatch Log Group
# 明示的に作成することで、保持ポリシーなどを管理可能
resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}
