output "ecr_repository_url" {
  description = "ECR Repository URL for this Lambda."
  value       = aws_ecr_repository.lambda_ecr_repo.repository_url
}

output "lambda_function_arn" {
  description = "ARN of this Lambda function."
  value       = aws_lambda_function.this.arn
}

output "lambda_function_name" {
  description = "Name of this Lambda function."
  value       = aws_lambda_function.this.function_name
}

output "lambda_invoke_arn" {
  description = "Invoke ARN of this Lambda function."
  value       = aws_lambda_function.this.invoke_arn
}

output "lambda_iam_role_arn" {
  description = "IAM Role ARN for this Lambda function."
  value       = aws_iam_role.lambda_exec_role.arn
}
