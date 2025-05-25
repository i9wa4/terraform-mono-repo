import asyncio
import json
import os
from typing import Any
from typing import Dict
import boto3

from mcp_client import GeminiMCPClient

# Lambda環境変数から設定を取得
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# MCP接続設定（環境変数から取得）
MCP_CONNECTIONS = {
    # "math": {
    #     "transport": "sse",
    #     "url": os.environ.get("MATH_SERVER_URL"),
    #     "headers": {"Authorization": f"Bearer {os.environ.get('MATH_SERVER_TOKEN')}"},
    # },
    # "weather": {"transport": "websocket", "url": os.environ.get("WEATHER_SERVER_URL")},
    # "database": {
    #     "transport": "sse",
    #     "url": os.environ.get("DATABASE_SERVER_URL"),
    #     "headers": {
    #         "Authorization": f"Bearer {os.environ.get('DATABASE_SERVER_TOKEN')}"
    #     },
    # },
}


async def process_query(event: Dict[str, Any]) -> Dict[str, Any]:
    """クエリを処理してレスポンスを返す"""

    # リクエストボディからメッセージを取得
    body = json.loads(event.get("body", "{}"))
    message = body.get("message", "")

    if not message:
        return {"statusCode": 400, "body": json.dumps({"error": "Message is required"})}

    client = GeminiMCPClient(
        gemini_api_key=GEMINI_API_KEY, mcp_connections=MCP_CONNECTIONS
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

    # 必要な環境変数をチェック
    if not GEMINI_API_KEY:
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"error": "GEMINI_API_KEY environment variable is required"}
            ),
        }

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
