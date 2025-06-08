import asyncio
import json
import logging
import os
from typing import Any
from typing import Dict

import boto3
from app.mcp_client import GeminiMCPClient
from botocore.exceptions import BotoCoreError

# ロガー設定
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


async def process_query(event: Dict[str, Any]) -> Dict[str, Any]:
    """クエリを処理してレスポンスを返す"""

    # ===== ここから: 初期化処理をすべてハンドラ内に移動 =====
    mcp_server_example_url_key = get_secret_value(
        os.environ.get("MCP_SERVER_EXAMPLE_SECRET_NAME"), "FUNCTION_URL"
    )
    gemini_api_key = get_secret_value(
        os.environ.get("COMMON_SECRET_NAME"), "GEMINI_API_KEY"
    )
    x_api_key = get_secret_value(os.environ.get("COMMON_SECRET_NAME"), "X_API_KEY")

    mcp_connections = {
        "mcp_server_example": {
            "transport": "sse",
            "url": mcp_server_example_url_key,
            "headers": {"X-Api-Key": x_api_key},
        },
    }
    # ===== ここまで: 初期化処理 =====

    # リクエストボディからメッセージを取得
    body = json.loads(event.get("body", "{}"))
    message = body.get("message", "")
    logger.info(f"Received message: {message}")

    if not message:
        return {"statusCode": 400, "body": json.dumps({"error": "Message is required"})}

    client = None  # finallyブロックのために定義
    try:
        client = GeminiMCPClient(
            gemini_api_key=gemini_api_key,
            mcp_connections=mcp_connections,
        )
        logger.info(
            f"Initialized GeminiMCPClient with connections: {mcp_connections.keys()}"
        )

        logger.info("Attempting to initialize client...")
        await client.initialize()
        logger.info("Client initialized successfully.")

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
            "servers_connected": list(mcp_connections.keys()),
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
                response_body_payload,
                ensure_ascii=False,
            ),
        }

    except Exception as e:
        logger.error(f"Error during query processing: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": str(e),
                    "details": "Check Lambda logs for mcp-client for more details.",
                }
            ),
        }

    finally:
        if client:
            await client.close()


def lambda_handler(event, context):
    """Lambda関数のエントリーポイント"""

    http_method = event.get("requestContext", {}).get("http", {}).get("method", "")

    if http_method == "POST":
        return asyncio.run(process_query(event))
    elif http_method == "GET":
        # ヘルスチェック
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "healthy"}),
        }
    else:
        return {"statusCode": 405, "body": json.dumps({"error": "Method not allowed"})}
