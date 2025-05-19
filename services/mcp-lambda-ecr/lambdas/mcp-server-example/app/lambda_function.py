# app/lambda_function.py (MCPサーバー)
import json
import logging

from app.request_handler import RequestHandler  # request_handler.pyからクラスをインポート

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info(f"MCP Server received event: {json.dumps(event)}")

    # Lambda関数URLのイベント構造はAPI Gatewayプロキシ統合に似ています
    # クライアントからの実際のクエリは event['body'] (POSTの場合) や
    # event (GETの場合) に含まれます
    # ここではクライアントがJSONボディでPOSTリクエストを送信すると仮定: { "query": "ユーザーの質問" }

    request_body_str = event.get("body", "{}")
    try:
        # Base64エンコードされている場合があるためデコードを試みる (API Gateway経由の場合など)
        if event.get("isBase64Encoded", False):
            import base64

            request_body_str = base64.b64decode(request_body_str).decode("utf-8")

        request_body = json.loads(request_body_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Error parsing request body: {e}", exc_info=True)
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid JSON in request body."}),
        }

    user_query = request_body.get("query")
    if not user_query:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Query is missing in request."}),
        }

    try:
        request_handler_instance = RequestHandler()
        # 実際の処理ロジックは request_handler.py に記述
        # [1, 6]には詳細がないためスタブを提供
        result = request_handler_instance.process_query(user_query)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                result
            ),  # 例: { "context": "処理された情報", "details": "..." }
        }
    except Exception as e:
        logger.error(f"Error processing query in MCP server: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Internal server error: {str(e)}"}),
        }
