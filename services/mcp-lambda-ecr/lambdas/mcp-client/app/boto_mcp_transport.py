import asyncio
import json
import logging
import re
from typing import Any, AsyncGenerator, Dict

import boto3
from botocore.eventstream import EventStream

logger = logging.getLogger(__name__)

# Boto3のクライアントはグローバルに一度だけ初期化
lambda_client = boto3.client("lambda")


class BotoMCPTransport:
    """boto3を使用してLambda経由でMCPサーバーと通信するトランスポート"""

    def __init__(self, function_name: str, api_key: str | None = None):
        if not function_name:
            raise ValueError("Lambda function_name is required.")
        self.function_name = function_name
        self.api_key = api_key

    def _create_lambda_payload(
        self, method: str, path: str, body: Dict | None = None
    ) -> Dict[str, Any]:
        """Mangumが期待するLambdaプロキシ統合ペイロードを作成"""
        payload = {
            "httpMethod": method,
            "path": path,
            "headers": {
                "Content-Type": "application/json",
                "Accept": "text/event-stream" if method == "GET" else "application/json",
            },
            "queryStringParameters": {},
            "body": json.dumps(body) if body else None,
            "isBase64Encoded": False,
        }
        if self.api_key:
            payload["headers"]["X-Api-Key"] = self.api_key
        return payload

    async def get_tools_stream(self) -> AsyncGenerator[Dict, None]:
        """
        サーバーにGETリクエストを送信し、SSEストリームを非同期で処理する。
        boto3のinvoke_with_response_streamは同期的なので、asyncioでラップする。
        """
        payload = self._create_lambda_payload("GET", "/mcp")

        def _invoke_in_executor():
            return lambda_client.invoke_with_response_stream(
                FunctionName=self.function_name,
                Payload=json.dumps(payload).encode("utf-8"),
                InvocationType="RequestResponse",
            )

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, _invoke_in_executor)

        event_stream: EventStream = response.get("EventStream")
        if not event_stream:
            logger.error("No EventStream in Lambda response.")
            return

        sse_data_pattern = re.compile(r"data: (.*)")
        for event in event_stream:
            if "PayloadChunk" in event:
                chunk = event["PayloadChunk"]["Payload"].decode("utf-8")
                match = sse_data_pattern.search(chunk)
                if match:
                    try:
                        yield json.loads(match.group(1))
                    except json.JSONDecodeError:
                        logger.error(f"Failed to decode SSE data chunk: {chunk}")
            elif "InvokeComplete" in event:
                logger.info("Lambda stream invocation complete.")
                break

    async def invoke_tool(self, tool_call: Dict) -> Dict:
        """サーバーにPOSTリクエストを送信してツールを実行する"""
        payload = self._create_lambda_payload("POST", "/mcp", body=tool_call)

        def _invoke_in_executor():
            return lambda_client.invoke(
                FunctionName=self.function_name,
                Payload=json.dumps(payload).encode("utf-8"),
                InvocationType="RequestResponse",
            )

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, _invoke_in_executor)

        response_payload_bytes = response["Payload"].read()
        response_payload = json.loads(response_payload_bytes.decode("utf-8"))

        # Lambdaプロキシ統合のレスポンスからbodyを抽出
        if "body" in response_payload:
            return json.loads(response_payload["body"])
        else:
            logger.error(f"Unexpected Lambda response format: {response_payload}")
            return {"error": "Invalid response format from server"} 