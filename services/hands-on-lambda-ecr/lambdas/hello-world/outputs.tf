output "ecr_repository_url" {
  description = "ECR Repository URL for this Lambda."
  value       = module.lambda_service.ecr_repository_url
}

output "lambda_function_arn" {
  description = "ARN of this Lambda function."
  value       = module.lambda_service.lambda_function_arn
}

output "lambda_function_name" {
  description = "Name of this Lambda function."
  value       = module.lambda_service.lambda_function_name
}

output "lambda_invoke_arn" {
  description = "Invoke ARN of this Lambda function."
  value       = module.lambda_service.lambda_invoke_arn
}

output "lambda_iam_role_arn" {
  description = "IAM Role ARN for this Lambda function."
  value       = module.lambda_service.lambda_iam_role_arn
}
