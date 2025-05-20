# services/mcp-lambda-ecr/lambdas/mcp-server-example/app/request_handler.py
import json
import random
import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

# MCPエラーコード (JSON-RPC 2.0 Specification + MCP独自)
MCP_PARSE_ERROR = -32700
MCP_INVALID_REQUEST = -32600
MCP_METHOD_NOT_FOUND = -32601
MCP_INVALID_PARAMS = -32602
MCP_INTERNAL_ERROR = -32603
MCP_TOOL_EXECUTION_ERROR = -32000  # MCP推奨のユーザー定義エラー範囲


# ツール定義
def echo_tool_func(params: Dict[str, Any], logger_instance) -> Dict[str, Any]:
    text_to_echo = params.get("text_to_echo")
    if text_to_echo is None:
        raise ValueError("Missing 'text_to_echo' parameter for echo_tool.")
    logger_instance.info(f"Echo tool called with: {text_to_echo}")
    return {"echoed_text": text_to_echo}


def static_info_tool_func(params: Dict[str, Any], logger_instance) -> Dict[str, Any]:
    topic = params.get("topic", "default_topic")
    logger_instance.info(f"Static info tool called for topic: {topic}")
    return {
        "info": (
            f"This is static MCP information about '{topic}' from mcp-server-example."
        )
    }


TOOLS_REGISTRY = {
    "echo_tool": {
        "function": echo_tool_func,
        "description": "Echoes back the input text provided in 'text_to_echo'.",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "text_to_echo": {"type": "string", "description": "The text to echo."}
            },
            "required": ["text_to_echo"],
        },
    },
    "static_info_tool": {
        "function": static_info_tool_func,
        "description": "Provides static information about a given 'topic'.",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic to get information about.",
                }
            },
            "required": ["topic"],
        },
    },
}


def create_jsonrpc_error(
    id_val: Optional[Union[str, int]],
    code: int,
    message: str,
    data: Optional[Any] = None,
) -> Dict[str, Any]:
    error_obj = {"code": code, "message": message}
    if data:
        error_obj["data"] = data
    return {"jsonrpc": "2.0", "error": error_obj, "id": id_val}


def create_jsonrpc_success(
    id_val: Optional[Union[str, int]], result_val: Any
) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "result": result_val, "id": id_val}


def dispatch_mcp_request(
    parsed_body: Dict[str, Any], lambda_context: Any, logger_instance: Any
) -> Dict[str, Any]:
    lambda_req_id = lambda_context.aws_request_id if lambda_context else "N/A"
    rpc_req_id = parsed_body.get("id")

    if parsed_body.get("jsonrpc") != "2.0":
        return create_jsonrpc_error(
            rpc_req_id, MCP_INVALID_REQUEST, "Invalid JSON-RPC version. Must be '2.0'."
        )

    method = parsed_body.get("method")
    params = parsed_body.get("params", {})

    logger_instance.info(
        f"LambdaReqID: {lambda_req_id}, RPCReqID: {rpc_req_id} - MCP Method: {method},"
        f" Params: {json.dumps(params)}"
    )

    if method == "mcp.discovery.list_tools":
        tools_list = [
            {
                "id": tool_name,
                "name": tool_name.replace("_", " ").title(),
                "description": tool_def.get("description"),
                "parameters_schema": tool_def.get("parameters_schema"),
            }
            for tool_name, tool_def in TOOLS_REGISTRY.items()
        ]
        return create_jsonrpc_success(rpc_req_id, {"tools": tools_list})

    elif method == "mcp.tools.call_tool":
        tool_id = params.get("tool_id")
        tool_params = params.get("params", {})

        if not tool_id or tool_id not in TOOLS_REGISTRY:
            logger_instance.error(
                f"LambdaReqID: {lambda_req_id}, RPCReqID: {rpc_req_id} - Tool not"
                f" found: {tool_id}"
            )
            return create_jsonrpc_error(
                rpc_req_id, MCP_METHOD_NOT_FOUND, f"Tool '{tool_id}' not found."
            )

        tool_def = TOOLS_REGISTRY[tool_id]
        try:
            # Future: Add parameter validation against tool_def["parameters_schema"]
            logger_instance.info(
                f"LambdaReqID: {lambda_req_id}, RPCReqID: {rpc_req_id} - Calling tool"
                f" '{tool_id}'"
            )
            time.sleep(random.uniform(0.05, 0.15))  # Simulate processing
            tool_result_data = tool_def["function"](tool_params, logger_instance)
            # MCP spec for mcp.CallToolResult: result is an object with a "content" field (string)
            return create_jsonrpc_success(
                rpc_req_id, {"content": json.dumps(tool_result_data)}
            )
        except ValueError as ve:
            logger_instance.error(
                f"LambdaReqID: {lambda_req_id}, RPCReqID: {rpc_req_id} - Invalid params"
                f" for '{tool_id}': {ve}"
            )
            return create_jsonrpc_error(
                rpc_req_id,
                MCP_INVALID_PARAMS,
                f"Invalid parameters for tool '{tool_id}': {str(ve)}",
            )
        except Exception as e:
            logger_instance.exception(
                f"LambdaReqID: {lambda_req_id}, RPCReqID: {rpc_req_id} - Error"
                f" executing tool '{tool_id}'."
            )
            return create_jsonrpc_error(
                rpc_req_id,
                MCP_TOOL_EXECUTION_ERROR,
                f"Error executing tool '{tool_id}': {str(e)}",
            )
    else:
        logger_instance.warning(
            f"LambdaReqID: {lambda_req_id}, RPCReqID: {rpc_req_id} - Unknown MCP"
            f" method: {method}"
        )
        return create_jsonrpc_error(
            rpc_req_id, MCP_METHOD_NOT_FOUND, f"Method '{method}' not found."
        )


def handle_request(
    event: Dict[str, Any], context: Any, logger_instance: Any
) -> Dict[str, Any]:
    lambda_req_id = context.aws_request_id if context else "N/A"
    logger_instance.info(f"LambdaReqID: {lambda_req_id} - Starting request handling.")
    response_headers = {"Content-Type": "application/json"}

    try:
        raw_body = event.get("body")
        if isinstance(raw_body, str):
            parsed_body = json.loads(raw_body)
        elif isinstance(raw_body, dict):
            parsed_body = raw_body
        else:
            logger_instance.error(
                f"LambdaReqID: {lambda_req_id} - Invalid or missing request body type:"
                f" {type(raw_body)}"
            )
            json_rpc_resp = create_jsonrpc_error(
                None, MCP_PARSE_ERROR, "Invalid or missing request body."
            )
            return {
                "statusCode": 400,
                "headers": response_headers,
                "body": json.dumps(json_rpc_resp),
            }

        json_rpc_resp = dispatch_mcp_request(parsed_body, context, logger_instance)

        http_status_code = 200
        if "error" in json_rpc_resp:
            error_code = json_rpc_resp.get("error", {}).get("code")
            if error_code in [
                MCP_PARSE_ERROR,
                MCP_INVALID_REQUEST,
                MCP_METHOD_NOT_FOUND,
                MCP_INVALID_PARAMS,
            ]:
                http_status_code = 400
            else:  # MCP_INTERNAL_ERROR, MCP_TOOL_EXECUTION_ERROR
                http_status_code = 500

        logger_instance.info(
            f"LambdaReqID: {lambda_req_id} - Responding with HTTP {http_status_code}."
        )
        return {
            "statusCode": http_status_code,
            "headers": response_headers,
            "body": json.dumps(json_rpc_resp),
        }

    except json.JSONDecodeError as e:
        logger_instance.error(
            f"LambdaReqID: {lambda_req_id} - JSONDecodeError in request body: {e}",
            exc_info=True,
        )
        json_rpc_resp = create_jsonrpc_error(
            None, MCP_PARSE_ERROR, "Invalid JSON in request body."
        )
        return {
            "statusCode": 400,
            "headers": response_headers,
            "body": json.dumps(json_rpc_resp),
        }
    except Exception as e:
        logger_instance.exception(
            f"LambdaReqID: {lambda_req_id} - Unexpected error in handle_request."
        )
        json_rpc_resp = create_jsonrpc_error(
            None, MCP_INTERNAL_ERROR, "An internal server error occurred."
        )
        return {
            "statusCode": 500,
            "headers": response_headers,
            "body": json.dumps(json_rpc_resp),
        }
