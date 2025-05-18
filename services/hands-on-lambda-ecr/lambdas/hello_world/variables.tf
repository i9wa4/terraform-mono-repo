variable "lambda_name_suffix" {
  description = "Suffix for the Lambda function name, used to construct the full name."
  type        = string
  default     = "hello_world" # Changed from example-lambda
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

variable "project_name" {
  description = "Name of the project. Should align with the common project name."
  type        = string
  default     = "hands-on-lambda-ecr"
}

variable "environment" {
  description = "Deployment environment (e.g., dev, prod). Should align with the environment setting."
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for deployments. This should be provided by the .tfvars file."
  type        = string
  # No default, expected from .tfvars
}

variable "common_tags" {
  description = "Common tags to apply to all resources. These are typically merged with lambda-specific tags."
  type        = map(string)
  default     = {
    Project     = "hands-on-lambda-ecr" # Default project, can be overridden by .tfvars
    ManagedBy   = "Terraform"
    # Environment tag is usually set specifically in .tfvars or by the provider block
  }
}
