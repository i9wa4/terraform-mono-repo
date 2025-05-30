import asyncio
import json
import logging
import os
from typing import Any
from typing import Dict

import boto3
from app.mcp_client import GeminiMCPClient
from botocore.exceptions import BotoCoreError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_secret_value(
    secret_name: str, secret_key: str, region_name: str = os.environ.get("AWS_REGION")
) -> str:
    """AWS Secrets Managerからシークレット値を取得"""
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret_payload = response["SecretString"]
        secret = json.loads(secret_payload)
        logger.info(
            f"Successfully retrieved secret '{secret_name}' (key: '{secret_key}')"
        )
        return secret[secret_key]
    except (BotoCoreError, json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error(
            f"Error processing secret '{secret_name}' (key: '{secret_key}'):"
            f" {type(e).__name__} - {str(e)}"
        )
        raise


mcp_server_example_url_key = get_secret_value(
    os.environ.get("MCP_SERVER_EXAMPLE_SECRET_NAME"), "FUNCTION_URL"
)

MCP_CONNECTIONS = {
    # "math": {
    #     "transport": "sse",
    #     "url": os.environ.get("MATH_SERVER_URL"),
    #     "headers": {"Authorization": f"Bearer {os.environ.get('MATH_SERVER_TOKEN')}"},
    # },
    # "weather": {
    #     "transport": "websocket",
    #     "url": os.environ.get("WEATHER_SERVER_URL")
    # },
    # "database": {
    #     "transport": "sse",
    #     "url": os.environ.get("DATABASE_SERVER_URL"),
    #     "headers": {
    #         "Authorization": f"Bearer {os.environ.get('DATABASE_SERVER_TOKEN')}"
    #     },
    # },
    "gitmcp": {
        "transport": "sse",
        "url": "https://gitmcp.io/langchain-ai/langchain-mcp-adapters",
    },
    "mcp_server_example": {"transport": "sse", "url": f"{mcp_server_example_url_key}"},
}


async def process_query(event: Dict[str, Any]) -> Dict[str, Any]:
    """クエリを処理してレスポンスを返す"""

    # リクエストボディからメッセージを取得
    body = json.loads(event.get("body", "{}"))
    message = body.get("message", "")
    logger.info(f"Received message: {message}")

    if not message:
        return {"statusCode": 400, "body": json.dumps({"error": "Message is required"})}

    client = GeminiMCPClient(
        gemini_api_key=get_secret_value(
            os.environ.get("THIS_SECRET_NAME"), "GEMINI_API_KEY"
        ),
        mcp_connections=MCP_CONNECTIONS,
    )
    logger.info(
        f"Initialized GeminiMCPClient with connections: {MCP_CONNECTIONS.keys()}"
    )

    try:
        await client.initialize()

        # クエリを実行
        logger.info(f"Querying with message: {message}")
        response_content_from_agent = await client.query(message)
        logger.info(f"Received response: {response_content_from_agent}")

        # 利用可能なツール情報も含める
        logger.info("Fetching available tools")
        available_tools = await client.get_available_tools()

        response_body_payload = {
            "response": response_content_from_agent,
            "available_tools": available_tools,
            "servers_connected": list(MCP_CONNECTIONS.keys()),
        }
        logger.info(
            "Final response body to be returned:"
            f" {json.dumps(response_body_payload, ensure_ascii=False)}"
        )

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                response_body_payload,  # 上で作成したペイロードを使用
                ensure_ascii=False,
            ),
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    finally:
        await client.close()


def lambda_handler(event, context):
    """Lambda関数のエントリーポイント"""

    # HTTPメソッドをチェック
    http_method = event.get("httpMethod", "")

    if http_method == "POST":
        # 非同期処理を実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(process_query(event))
        finally:
            loop.close()
    elif http_method == "GET":
        # ヘルスチェック
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "status": "healthy",
                    "servers_configured": list(MCP_CONNECTIONS.keys()),
                }
            ),
        }
    else:
        return {"statusCode": 405, "body": json.dumps({"error": "Method not allowed"})}
