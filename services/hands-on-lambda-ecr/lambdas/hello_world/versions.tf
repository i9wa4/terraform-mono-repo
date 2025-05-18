terraform {
  required_version = "~> 1.11.4" # Or your preferred version constraint

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0" # Or your preferred version constraint
    }
  }

  backend "s3" {
    bucket  = "i9wa4-terraform" # Replace with your S3 bucket name
    key     = "hands-on-lambda-ecr/lambdas/hello_world/terraform.tfstate" # Unique key for this lambda's state
    region  = "ap-northeast-1"  # Replace with your S3 bucket region
    encrypt = true
    # use_lockfile = true # This is a CLI argument for init, not a backend config option
  }
}
