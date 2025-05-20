# services/mcp-lambda-ecr/lambdas/mcp-client/app/lambda_function.py
import json
import logging

from app.config import AppConfig
from app.gemini_service import GeminiService
from app.mcp_service import MCPService
from app.mcp_service import MCPServiceError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set for the root logger if not configured elsewhere

# Initialize config globally to catch errors early (on cold start)
try:
    config = AppConfig()
    logger.info("AppConfig loaded successfully.")
except ValueError as e:  # Catch specific config loading errors
    logger.critical(f"CRITICAL - Failed to initialize AppConfig: {e}", exc_info=True)
    # This will cause subsequent invocations to fail if config is needed,
    # or Lambda init to fail if this code is run at module import time and raises.
    config = None  # Ensure config is None if init fails.


def create_lambda_response(status_code: int, body_dict: dict) -> dict:
    """Helper to create Lambda proxy integration response."""
    return {
        "statusCode": status_code,
        "body": json.dumps(body_dict),
        "headers": {"Content-Type": "application/json"},
    }


def lambda_handler(event, context):
    lambda_req_id = context.aws_request_id if context else "N/A_CONTEXT"
    logger.info(f"LambdaReqID: {lambda_req_id} - Received event: {json.dumps(event)}")

    if config is None:  # Check if global config failed
        logger.error(f"LambdaReqID: {lambda_req_id} - AppConfig not loaded. Aborting.")
        return create_lambda_response(
            500, {"error": "Server configuration error", "request_id": lambda_req_id}
        )

    try:
        # 1. Parse input payload
        if isinstance(event.get("body"), str):
            try:
                payload = json.loads(event["body"])
            except json.JSONDecodeError as e:
                logger.error(
                    f"LambdaReqID: {lambda_req_id} - Invalid JSON in event body: {e}",
                    exc_info=True,
                )
                return create_lambda_response(
                    400, {"error": "Invalid JSON in request body", "details": str(e)}
                )
        else:  # Direct invocation (e.g., Lambda test console)
            payload = event

        user_query = payload.get("user_query")
        tool_info = payload.get(
            "tool_to_call"
        )  # Expects {"tool_id": "...", "params": {...}}

        if (
            not user_query
            or not tool_info
            or not isinstance(tool_info, dict)
            or not tool_info.get("tool_id")
        ):
            logger.error(
                f"LambdaReqID: {lambda_req_id} - Missing 'user_query' or valid"
                f" 'tool_to_call' (with 'tool_id'). Payload: {payload}"
            )
            return create_lambda_response(
                400,
                {"error": "Missing 'user_query' or valid 'tool_to_call' structure."},
            )

        mcp_tool_id = tool_info["tool_id"]
        mcp_tool_params = tool_info.get(
            "params", {}
        )  # Params for the specific MCP tool

        logger.info(
            f"LambdaReqID: {lambda_req_id} - User Query: '{user_query}', Tool:"
            f" '{mcp_tool_id}', Tool Params: {json.dumps(mcp_tool_params)}"
        )

        # 2. Interact with MCP Server
        mcp_service = MCPService(config.mcp_server_url)
        # mcp_service.call_tool returns the "result" part of JSON-RPC, e.g. {"content": ...}
        mcp_tool_result = mcp_service.call_tool(mcp_tool_id, mcp_tool_params)
        logger.info(
            f"LambdaReqID: {lambda_req_id} - MCP Tool '{mcp_tool_id}' raw result:"
            f" {json.dumps(mcp_tool_result)}"
        )

        # Extract content from tool result for Gemini
        # The content is already parsed from JSON string by mcp_service if it was a string
        actual_context_from_mcp = mcp_tool_result.get("content")

        if actual_context_from_mcp is None:
            logger.warning(
                f"LambdaReqID: {lambda_req_id} - Tool '{mcp_tool_id}' did not return"
                " 'content' in its result."
            )
            # Decide fallback: use user_query, an empty string, or a message.
            text_for_gemini_prompt = (
                f"The user asked: '{user_query}'. The tool '{mcp_tool_id}' did not"
                " provide specific context. Please answer based on general knowledge"
                " or indicate context is missing."
            )
        elif isinstance(actual_context_from_mcp, (dict, list)):
            text_for_gemini_prompt = (
                f"User query: '{user_query}'\n\nContext from tool"
                f" '{mcp_tool_id}':\n{json.dumps(actual_context_from_mcp, indent=2)}"
            )
        else:  # string or other primitive
            text_for_gemini_prompt = (
                f"User query: '{user_query}'\n\nContext from tool"
                f" '{mcp_tool_id}':\n{str(actual_context_from_mcp)}"
            )

        # 3. Process with Gemini
        gemini_service = GeminiService(config.gemini_api_key)
        summary = gemini_service.summarize(text_for_gemini_prompt)
        logger.info(
            f"LambdaReqID: {lambda_req_id} - Gemini Summary: {summary[:300]}..."
        )  # Log a preview

        # 4. Formulate and return final response
        final_response = {
            "request_id": lambda_req_id,
            "user_query": user_query,
            "tool_called": mcp_tool_id,
            "tool_params_sent": mcp_tool_params,
            "mcp_tool_result_content": actual_context_from_mcp,  # The content part
            "text_provided_to_gemini": text_for_gemini_prompt,
            "gemini_summary": summary,
        }
        return create_lambda_response(200, final_response)

    except MCPServiceError as e:
        logger.error(
            f"LambdaReqID: {lambda_req_id} - MCPServiceError: {e.args[0]} (HTTP Status:"
            f" {e.status_code}, RPC Error Code: {e.rpc_error_code})",
            exc_info=True,
        )
        error_info = {"message": f"Error during MCP interaction: {e.args[0]}"}
        if e.error_payload:
            error_info["mcp_server_error_details"] = e.error_payload
        return create_lambda_response(
            e.status_code or 502, {"error": error_info, "request_id": lambda_req_id}
        )  # 502 Bad Gateway if MCP server fails
    except ValueError as e:  # For config, Gemini, or other validation errors
        logger.error(f"LambdaReqID: {lambda_req_id} - ValueError: {e}", exc_info=True)
        return create_lambda_response(
            400,
            {
                "error": "Invalid input or configuration error",
                "details": str(e),
                "request_id": lambda_req_id,
            },
        )
    except Exception as e:  # Catch-all for unexpected errors
        logger.critical(
            f"LambdaReqID: {lambda_req_id} - Unexpected critical error: {e}",
            exc_info=True,
        )
        return create_lambda_response(
            500,
            {
                "error": "Internal server error",
                "details": str(e),
                "request_id": lambda_req_id,
            },
        )
