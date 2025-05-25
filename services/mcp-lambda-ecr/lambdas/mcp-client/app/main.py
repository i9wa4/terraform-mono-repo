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
    "gitmcp": {"transport": "websocket", "url": "https://gitmcp.io/docs"}
}


def get_secret_value(
    secret_name: str, secret_key: str, region_name: str = os.environ.get("AWS_REGION")
) -> str:
    """AWS Secrets Managerからシークレット値を取得"""
    client = boto3.client(service_name="secretsmanager", region_name=region_name)
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret_payload = response["SecretString"]
        secret = json.loads(secret_payload)
        return secret[secret_key]
    except (BotoCoreError, json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error(
            f"Error processing secret '{secret_name}' (key: '{secret_key}'):"
            f" {type(e).__name__} - {str(e)}"
        )
        raise


async def process_query(event: Dict[str, Any]) -> Dict[str, Any]:
    """クエリを処理してレスポンスを返す"""

    # リクエストボディからメッセージを取得
    body = json.loads(event.get("body", "{}"))
    message = body.get("message", "")

    if not message:
        return {"statusCode": 400, "body": json.dumps({"error": "Message is required"})}

    client = GeminiMCPClient(
        gemini_api_key=get_secret_value("THIS_SECRET_NAME", "GEMINI_API_KEY"),
        mcp_connections=MCP_CONNECTIONS,
    )

    try:
        await client.initialize()

        # クエリを実行
        response = await client.query(message)

        # 利用可能なツール情報も含める
        available_tools = await client.get_available_tools()

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "response": response,
                    "available_tools": available_tools,
                    "servers_connected": list(MCP_CONNECTIONS.keys()),
                }
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
