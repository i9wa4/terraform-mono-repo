variable "aws_region" {
  description = "デプロイ先のAWSリージョン"
  type        = string
  default     = "ap-northeast-1"
}

variable "project_name" {
  description = "プロジェクト名"
  type        = string
  default     = "hands-on-lambda-ecr"
}

variable "aws_account_id" {
  type        = string
  description = "AWS Account ID where the OIDC provider is located."
  default     = "000000000000"
}

variable "github_oidc_provider_url" {
  type        = string
  description = "The URL of the GitHub OIDC provider (e.g., token.actions.githubusercontent.com)."
  default     = "token.actions.githubusercontent.com"
}

variable "github_repository" {
  type        = string
  description = "The GitHub repository (e.g., your-org/your-repo) allowed to assume this role."
  default     = "i9wa4/terraform-mono-repo"
}

variable "role_name" {
  type        = string
  description = "Name of the IAM role."
  default     = "hands-on-lambda-ecr"
}

variable "ecr_repository_name" {
  description = "ECRリポジトリ名"
  type        = string
  default     = "hands-on-lambda-ecr"
}

variable "lambda_function_name" {
  description = "Lambda関数名"
  type        = string
  default     = "hello-world-python-container"
}

variable "ecr_image_uri" {
  description = "Lambda関数のECRイメージURI (デプロイ時に設定する)"
  type        = string
  default     = "dummy"
}

variable "environment" {
  description = "デプロイ環境 (例: dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "log_retention_days" {
  description = "CloudWatchログの保持日数"
  type        = number
  default     = 7
}
