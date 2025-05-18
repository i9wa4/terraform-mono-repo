variable "lambda_name_suffix" {
  description = "Suffix for the Lambda function name, used to construct the full name."
  type        = string
  default     = "hello-world"
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
  description = "Name of the project. This is used to construct resource names and tags."
  type        = string
  default     = "hands-on-lambda-ecr" # Default value, can be overridden by .tfvars
}

variable "environment" {
  description = "Deployment environment (e.g., dev, prod). This is used for naming and tagging."
  type        = string
  default     = "dev" # Default value, can be overridden by .tfvars
}

variable "aws_region" {
  description = "AWS region for the Lambda deployment. This should be provided by the .tfvars file."
  type        = string
  # No default, as this is a fundamental setting expected from the environment configuration.
}

variable "common_tags" {
  description = "Common tags to apply to resources, typically passed from a central .tfvars file."
  type        = map(string)
  default     = {
    Project     = "hands-on-lambda-ecr" # Default project tag
    ManagedBy   = "Terraform"
    Environment = "dev"                 # Default environment tag
  }
}

