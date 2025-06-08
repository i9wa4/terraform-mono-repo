variable "project_name" {
  description = "The name of the project."
  type        = string
  default     = "mcp-lambda-ecr"
}

variable "environment" {
  description = "The environment for the deployment (e.g., dev, stg, prod)."
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for deployment."
  type        = string
}

variable "github_repository" {
  description = "The GitHub repository (e.g., your-org/your-repo) allowed to assume this role."
  type        = string
}

variable "image_uri" {
  description = "ECR image URI for the Lambda. Provided in deployment."
  type        = string
  # No default.
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days."
  type        = number
  default     = 7
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB."
  type        = number
  default     = 1024
  default     = 256
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds."
  type        = number
  default     = 30
}

variable "lambda_architecture" {
  description = "Lambda function architecture. Should match the Docker build architecture."
  type        = string
  default     = "arm64"
}
