import asyncio
import json
import logging
import os

from app.aws_utils import get_secret_value
from app.mcp_client import GeminiMCPClient

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --- Environment Variables ---
# These should be configured in your Lambda environment settings
MCP_SERVER_EXAMPLE_SECRET_NAME = os.environ.get("MCP_SERVER_EXAMPLE_SECRET_NAME")
COMMON_SECRET_NAME = os.environ.get("COMMON_SECRET_NAME")

# --- Initialize Client at Cold Start ---
client = None
try:
    # Retrieve secrets using the helper function
    function_url = get_secret_value(MCP_SERVER_EXAMPLE_SECRET_NAME, "FUNCTION_URL")
    gemini_api_key = get_secret_value(COMMON_SECRET_NAME, "GEMINI_API_KEY")
    x_api_key = get_secret_value(COMMON_SECRET_NAME, "X_API_KEY")

    if not all([function_url, gemini_api_key, x_api_key]):
        raise ValueError("One or more required secrets could not be retrieved.")

    # Initialize the GeminiMCPClient with the retrieved secrets
    client = GeminiMCPClient(
        gemini_api_key=gemini_api_key,
        mcp_connections={
            "mcp_server_example": {
                "transport": "sse",
                "url": function_url,
                "headers": {"X-Api-Key": x_api_key},
            }
        },
    )
    logger.info("Successfully initialized GeminiMCPClient.")

except Exception as e:
    logger.error(
        f"Failed to initialize GeminiMCPClient at cold start: {e}", exc_info=True
    )


async def process_query(query: str):
    """Initializes client if needed and processes the user query."""
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
        # Assuming the query is in the 'body' of a JSON payload
        body = json.loads(event.get("body", "{}"))
        # "query" の代わりに "message" キーから値を取得するように修正
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
