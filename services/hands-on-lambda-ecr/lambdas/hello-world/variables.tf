# --- Common variables (often sourced from a shared .tfvars file) ---
variable "project_name" {
  description = "Name of the project. Used for resource names and tags."
  type        = string
  default     = "hands-on-lambda-ecr" # Can be overridden by .tfvars.
}

variable "environment" {
  description = "Deployment environment (e.g., dev, prod). Used for naming and tagging."
  type        = string
  default     = "dev" # Can be overridden by .tfvars.
}

variable "aws_region" {
  description = "AWS region for Lambda deployment. Expected from .tfvars file."
  type        = string
  # No default; fundamental setting.
}

variable "common_tags" {
  description = "Common tags for resources. Merged with lambda-specific tags."
  type        = map(string)
  default = {
    Project     = "hands-on-lambda-ecr" # Default project tag.
    ManagedBy   = "Terraform"
    # The Environment tag will be explicitly set using var.environment in default_tags.
  }
}

variable "aws_account_id" {
  description = "AWS Account ID. Typically from .tfvars; declared here to silence warnings."
  type        = string
}

variable "github_repository" {
  description = "GitHub repository (e.g., org/repo). Typically from .tfvars; declared here to silence warnings."
  type        = string
}

# --- Lambda-specific variables ---
variable "lambda_name_suffix" {
  description = "Suffix for the Lambda function name, used to construct the full name."
  type        = string
  default     = "hello-world"
}

variable "image_uri" {
  description = "ECR image URI for the Lambda. Provided by Makefile at deployment."
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
  default     = 256
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds."
  type        = number
  default     = 30
}

