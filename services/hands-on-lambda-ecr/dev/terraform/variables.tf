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
