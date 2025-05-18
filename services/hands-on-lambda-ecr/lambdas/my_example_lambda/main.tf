provider "aws" {
  region = var.aws_region
  default_tags {
    tags = merge(
      {
        Project     = var.project_name
        Environment = var.environment
        LambdaName  = var.lambda_name_suffix
      },
      var.common_tags
    )
  }
}

module "lambda_service" {
  source = "../../modules/lambda_service" # Relative path to the module

  function_name      = "${var.project_name}-${var.environment}-${var.lambda_name_suffix}"
  image_uri          = var.image_uri       # This will be passed by Makefile/CI
  aws_region         = var.aws_region
  log_retention_days = var.log_retention_days
  lambda_memory_size = var.lambda_memory_size
  lambda_timeout     = var.lambda_timeout
  tags               = var.common_tags # Pass common_tags to the module
}
