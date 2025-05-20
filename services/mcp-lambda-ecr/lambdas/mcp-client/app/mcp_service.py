# services/mcp-lambda-ecr/lambdas/mcp-client/app/mcp_service.py
import json
import logging
import os
import uuid

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.exceptions import NoCredentialsError
from botocore.exceptions import PartialCredentialsError

logger = logging.getLogger(__name__)


class MCPServiceError(Exception):
    """Custom exception for MCPService errors, potentially holding status and payload."""

    def __init__(
        self, message, status_code=None, error_payload=None, rpc_error_code=None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.error_payload = error_payload
        self.rpc_error_code = rpc_error_code


class MCPService:
    def __init__(self, server_url: str):
        self.server_url = server_url
        if not self.server_url:
            logger.error("MCPService initialized with an empty server_url.")
            raise ValueError("MCP Server URL is required and cannot be empty.")

        try:
            self.session = boto3.Session()
            self.credentials = self.session.get_credentials()
            if self.credentials is None:
                raise ValueError("Could not load AWS credentials from session.")

            self.frozen_credentials = self.credentials.get_frozen_credentials()
            if self.frozen_credentials is None:
                raise ValueError("Could not obtain frozen AWS credentials.")

            self.aws_region = os.environ.get("AWS_REGION") or self.session.region_name
            if not self.aws_region:
                raise ValueError(
                    "AWS Region could not be determined. Set AWS_REGION or configure"
                    " session region."
                )
            logger.info(
                f"MCPService initialized. URL: {self.server_url}, Region:"
                f" {self.aws_region}"
            )
        except (
            NoCredentialsError,
            PartialCredentialsError,
            ValueError,
        ) as e:  # Catch specific init errors
            logger.error(
                f"Error initializing MCPService credentials or config: {e}",
                exc_info=True,
            )
            raise  # Re-raise as a critical setup failure

    def _send_request(self, method_name: str, params: dict) -> dict:
        """Internal method to send a JSON-RPC request with SigV4 signing."""
        rpc_request_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "method": method_name,
            "params": params,
            "id": rpc_request_id,
        }
        logger.info(
            f"Sending MCP Request ID {rpc_request_id} to {self.server_url}:"
            f" Method='{method_name}', Params='{json.dumps(params)}'"
        )

        try:
            aws_http_request = AWSRequest(
                method="POST",
                url=self.server_url,
                data=json.dumps(payload),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            SigV4Auth(self.frozen_credentials, "lambda", self.aws_region).add_auth(
                aws_http_request
            )
            prepared_request = aws_http_request.prepare()

            response = requests.request(
                method=prepared_request.method,
                url=prepared_request.url,
                headers=prepared_request.headers,
                data=prepared_request.body,
                timeout=30,  # Increased timeout
            )
            logger.info(
                f"MCP Response for ID {rpc_request_id}: Status={response.status_code},"
                f" Headers='{response.headers.get('Content-Type')}'"
            )

            # Regardless of HTTP status for JSON-RPC, try to parse JSON if content type suggests it
            if "application/json" in response.headers.get("Content-Type", "").lower():
                response_json = response.json()
            else:  # If not JSON, treat as an error with raw text
                logger.error(
                    f"MCP server returned non-JSON response for ID {rpc_request_id}."
                    f" Status: {response.status_code}, Content: {response.text[:500]}"
                )
                raise MCPServiceError(
                    "MCP server returned non-JSON response (Status:"
                    f" {response.status_code})",
                    status_code=response.status_code,
                    error_payload=response.text,
                )

            # Check for JSON-RPC level errors (even if HTTP 200)
            if "error" in response_json:
                rpc_error = response_json["error"]
                rpc_error_code = rpc_error.get("code")
                rpc_error_message = rpc_error.get("message", "Unknown RPC error")
                logger.error(
                    f"MCP JSON-RPC Error for ID {rpc_request_id}:"
                    f" Code={rpc_error_code}, Message='{rpc_error_message}'"
                )
                raise MCPServiceError(
                    f"MCP RPC Error: {rpc_error_message}",
                    status_code=response.status_code,  # HTTP status might be 200
                    error_payload=rpc_error,
                    rpc_error_code=rpc_error_code,
                )

            if (
                "result" not in response_json
            ):  # Should not happen if no error and valid JSON-RPC
                logger.error(
                    f"MCP Invalid JSON-RPC (missing 'result') for ID {rpc_request_id}:"
                    f" {response_json}"
                )
                raise MCPServiceError(
                    "Invalid JSON-RPC response (missing 'result')",
                    status_code=response.status_code,
                    error_payload=response_json,
                )

            # Check if the RPC ID in response matches (optional, but good practice)
            if response_json.get("id") != rpc_request_id:
                logger.warning(
                    f"MCP RPC ID mismatch for request {rpc_request_id}. Response ID:"
                    f" {response_json.get('id')}"
                )

            return response_json  # Contains 'result', 'id', 'jsonrpc'

        except requests.exceptions.JSONDecodeError as e:
            logger.error(
                f"Failed to decode JSON response for ID {rpc_request_id} from MCP"
                " server. Status:"
                f" {response.status_code if 'response' in locals() else 'N/A'}, Body:"
                f" {response.text[:500] if 'response' in locals() else 'N/A'}",
                exc_info=True,
            )
            raise MCPServiceError(
                f"Invalid JSON response from MCP server: {e}",
                status_code=response.status_code if "response" in locals() else None,
            ) from e
        except (
            requests.exceptions.RequestException
        ) as e:  # Catches ConnectionError, Timeout, etc.
            logger.error(
                f"MCP Request failed for ID {rpc_request_id}: {e}", exc_info=True
            )
            raise MCPServiceError(f"MCP communication failure: {e}") from e
        # MCPServiceError is re-raised if caught above

    def list_tools(self) -> dict:
        """Calls mcp.discovery.list_tools. Returns the 'result' field of the JSON-RPC response."""
        # MCP standard: list_tools has no parameters
        full_response = self._send_request(
            method_name="mcp.discovery.list_tools", params={}
        )
        return full_response.get("result", {})  # e.g., {"tools": [...]}

    def call_tool(self, tool_id: str, tool_params: dict) -> dict:
        """
        Calls mcp.tools.call_tool. Expects tool_params for the specific tool.
        Returns the 'result' field (e.g., {"content": "..."}) of the JSON-RPC response.
        The "content" is typically a JSON string, so it's parsed here.
        """
        mcp_standard_params = {
            "tool_id": tool_id,
            "params": tool_params,  # These are the parameters for the tool itself
        }
        full_response = self._send_request(
            method_name="mcp.tools.call_tool", params=mcp_standard_params
        )
        tool_result_payload = full_response.get(
            "result", {}
        )  # e.g., {"content": "{\"key\":\"value\"}"}

        if "content" in tool_result_payload:
            content_str = tool_result_payload["content"]
            if isinstance(content_str, str):
                try:
                    # The content from the tool is often a JSON string
                    tool_result_payload["content"] = json.loads(content_str)
                except json.JSONDecodeError:
                    logger.warning(
                        f"Content from tool '{tool_id}' was a string but not valid"
                        f" JSON: '{content_str[:100]}...'"
                    )
                    # Keep it as a string if not parsable as JSON
            # If content is already a dict/list (not per strict MCP spec for content but possible), leave as is
        return tool_result_payload
