output "mcp_server_example_url" {
  description = "MCP Server Example's URL"
  value = aws_lambda_function_url.this.function_url
}
