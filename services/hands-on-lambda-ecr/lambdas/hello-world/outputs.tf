output "aws_account_id" {
  description = "AWS Account ID."
  value       = data.aws_caller_identity.current.account_id
}
