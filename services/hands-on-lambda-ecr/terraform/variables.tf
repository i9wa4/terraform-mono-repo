variable "project_name" {
  description = "The name of the project."
  type        = string
  default     = "hands-on-lambda-ecr"
}

variable "environment" {
  description = "The environment for the deployment (e.g., dev, staging, prod)."
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for deployment."
  type        = string
}

variable "aws_account_id" {
  description = "AWS Account ID where the OIDC provider is located."
  type        = string
}

variable "github_repository" {
  description = "The GitHub repository (e.g., your-org/your-repo) allowed to assume this role."
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources."
  type        = map(string)
  default = {
    Project   = "hands-on-lambda-ecr"
    ManagedBy = "Terraform"
    # Environment tag can be added here or overridden by environment-specific .tfvars
  }
}

# --- Specific variables for this configuration ---

variable "github_oidc_provider_url" {
  description = "The URL of the GitHub OIDC provider (e.g., token.actions.githubusercontent.com)."
  type        = string
  default     = "token.actions.githubusercontent.com"
}

variable "github_actions_role_name" {
  description = "Name of the IAM role for GitHub Actions OIDC."
  type        = string
  default     = "hands-on-lambda-ecr"
}

