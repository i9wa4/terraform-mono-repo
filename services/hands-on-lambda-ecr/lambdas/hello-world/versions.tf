terraform {
  required_version = "~> 1.11.4"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    # bucket is configured by Makefile during init
    key     = "hands-on-lambda-ecr/lambdas/hello-world/terraform.tfstate" # Unique key for this lambda's state
    region  = "ap-northeast-1"                                            # S3 bucket region
    encrypt = true
  }
}
