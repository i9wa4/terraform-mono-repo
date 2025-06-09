import asyncio
import json
import logging
import os

from app.aws_utils import get_secret_value
# このファイルは mcp-client のため、mcp_client の import が必要です
from app.mcp_client import GeminiMCPClient

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# --- Environment Variables ---
MCP_SERVER_EXAMPLE_SECRET_NAME = os.environ.get("MCP_SERVER_EXAMPLE_SECRET_NAME")
COMMON_SECRET_NAME = os.environ.get("COMMON_SECRET_NAME")

# --- Initialize Client at Cold Start ---
client = None
try:
    # サーバーのLambda関数名をシークレットから取得
    server_function_name = get_secret_value(
        MCP_SERVER_EXAMPLE_SECRET_NAME, "FUNCTION_NAME"
    )
    gemini_api_key = get_secret_value(COMMON_SECRET_NAME, "GEMINI_API_KEY")
    # APIキーはboto3の認証に含まれるため不要だが、将来的な利用を想定して残す
    x_api_key = get_secret_value(COMMON_SECRET_NAME, "X_API_KEY")

    if not all([server_function_name, gemini_api_key, x_api_key]):
        logger.error(
            "Failed to retrieve one or more required values: "
            f"server_function_name={server_function_name}, "
            f"gemini_api_key is_set={bool(gemini_api_key)}, "
            f"x_api_key is_set={bool(x_api_key)}"
        )
        raise ValueError("One or more required secrets could not be retrieved.")

    logger.info(f"Target server Lambda function: {server_function_name}")

    client = GeminiMCPClient(
        gemini_api_key=gemini_api_key,
        server_function_name=server_function_name,
        server_api_key=x_api_key,  # APIキーを渡す
    )
    logger.info("Successfully initialized GeminiMCPClient with BotoMCPTransport.")

except Exception as e:
    logger.error(
        f"Failed to initialize GeminiMCPClient at cold start: {e}", exc_info=True
    )


async def process_query(query: str):
    if not client:
        raise RuntimeError(
            "Client is not initialized. Check cold start logs for errors."
        )

    logger.info("Initializing client for the request...")
    await client.initialize()

    logger.info(f"Processing query: {query}")
    response_chunks = []
    async for chunk in client.astream(query):
        response_chunks.append(chunk)

    logger.info("Closing client resources.")
    await client.close()

    return "".join(map(str, response_chunks))


def lambda_handler(event, context):
    """AWS Lambda handler function."""
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        body = json.loads(event.get("body", "{}"))
        query = body.get("message")

        if not query:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Query not provided in request body."}),
            }

        result = asyncio.run(process_query(query))

        return {"statusCode": 200, "body": json.dumps({"response": result})}

    except Exception as e:
        logger.error(f"Error during query processing: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }
