variable "project_name" {
  description = "The name of the project."
  type        = string
  default     = "hands-on-lambda-ecr"
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

variable "github_oidc_provider_url" {
  description = "The URL of the GitHub OIDC provider."
  type        = string
  default     = "token.actions.githubusercontent.com"
}

variable "lambda_app_names" {
  description = "A list of Lambda application names to create ECR repositories for (e.g., [\"requester\", \"another-app\"])"
  type        = list(string)
  default     = []
}
