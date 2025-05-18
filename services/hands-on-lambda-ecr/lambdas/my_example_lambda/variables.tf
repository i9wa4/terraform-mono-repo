variable "aws_region" {
  description = "AWS region for deployment."
  type        = string
}

variable "project_name" {
  description = "Name of the project."
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g., dev, prod)."
  type        = string
}

variable "lambda_name_suffix" {
  description = "Suffix for the Lambda function name, used to construct the full name."
  type        = string
  default     = "example-lambda"
}

variable "image_uri" {
  description = "The ECR image URI for the Lambda function. This should be provided at deployment time."
  type        = string
  # No default, must be provided by the caller (e.g., Makefile)
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days."
  type        = number
  default     = 7
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB."
  type        = number
  default     = 256
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds."
  type        = number
  default     = 30
}

variable "common_tags" {
  description = "Common tags to apply to all resources."
  type        = map(string)
  default     = {}
}
