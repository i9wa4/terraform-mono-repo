terraform {
  required_version = "~> 1.11.4" # Or your preferred version constraint

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0" # Or your preferred version constraint
    }
  }

  backend "s3" {
    bucket  = "i9wa4-terraform"                                 # Replace with your S3 bucket name
    key     = "hands-on-lambda-ecr/terraform/terraform.tfstate" # Unique key for CI/CD state
    region  = "ap-northeast-1"                                  # Replace with your S3 bucket region
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region
}
