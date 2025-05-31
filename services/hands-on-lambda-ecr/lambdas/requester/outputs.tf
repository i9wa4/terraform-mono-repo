output "requester_lambda_function_url_output" {
  description = "The Function URL for the requester Lambda."
  value       = aws_lambda_function_url.requester_function_url.function_url
}
