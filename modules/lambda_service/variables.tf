variable "function_name" {
  description = "The name for the Lambda function, ECR repository, and related IAM resources."
  type        = string
}

variable "image_uri" {
  description = "The ECR image URI for the Lambda function."
  type        = string
}

variable "aws_region" {
  description = "AWS region for deployments."
  type        = string
}

variable "tags" {
  description = "A map of tags to assign to created resources."
  type        = map(string)
  default     = {}
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
