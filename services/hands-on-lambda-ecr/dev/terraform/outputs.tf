output "ecr_repository_url" {
  description = "ECRリポジトリのURL"
  value       = aws_ecr_repository.app_ecr_repo.repository_url
}

output "lambda_function_arn" {
  description = "Lambda関数のARN"
  value       = aws_lambda_function.hello_world_lambda.arn
}

output "lambda_function_name" {
  description = "Lambda関数の名前"
  value       = aws_lambda_function.hello_world_lambda.function_name
}

output "lambda_invoke_arn" {
  description = "Lambda関数の呼び出しARN"
  value       = aws_lambda_function.hello_world_lambda.invoke_arn
}

output "lambda_iam_role_arn" {
  description = "Lambda関数のIAMロールARN"
  value       = aws_iam_role.lambda_exec_role.arn
}
