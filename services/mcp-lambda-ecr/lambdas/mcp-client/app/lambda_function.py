# app/lambda_function.py
import json
import logging

from app.config import AppConfig
from app.gemini_service import GeminiService
from app.mcp_service import MCPService
from app.slack_service import SlackService

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AppConfigのインスタンスはLambdaのグローバルスコープで初期化することで、
# 複数回の呼び出しでSecrets Managerへのアクセスをキャッシュする効果が期待できる
# (Lambda Extensionを使用しない場合の簡易的なキャッシュ)
# ただし、シークレットのローテーションを考慮する場合はTTLを設けるなどの工夫が必要
try:
    config = AppConfig()
except Exception as e:
    logger.critical(f"Failed to initialize AppConfig: {e}", exc_info=True)
    # 設定読み込み失敗時はLambdaの初期化で失敗させる
    raise


def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # 設定を環境変数から読み込み
        config = AppConfig()

        # 1. Slackイベントからユーザーのクエリを抽出 (実際の構造に依存)
        #    ここではSlash Commandのペイロードを想定
        #    Slackからのリクエストボディは通常URLエンコードされているため、パースが必要な場合がある
        if isinstance(event.get("body"), str):
            try:
                # API Gateway経由の場合、bodyが文字列化されたJSONのことがある
                slack_payload = json.loads(event["body"])
            except json.JSONDecodeError:
                # application/x-www-form-urlencoded の場合
                from urllib.parse import parse_qs

                slack_payload = {k: v for k, v in parse_qs(event["body"]).items()}
        else:
            slack_payload = event.get("body", {})

        user_query = slack_payload.get("text")
        slack_response_url = slack_payload.get("response_url")

        if not user_query or not slack_response_url:
            logger.error("Missing user_query or slack_response_url")
            return {
                "statusCode": 400,
                "body": json.dumps({"text": "リクエストが無効です。"}),
            }

        # 2. MCPサーバーに接続
        mcp_service = MCPService(config.mcp_server_url)
        mcp_response = mcp_service.ask(user_query)
        logger.info(f"MCP Server Response: {mcp_response}")

        # 3. Gemini APIから要約を取得
        gemini_service = GeminiService(config.gemini_api_key)
        # mcp_responseから要約対象のテキストを抽出するロジックが必要
        text_to_summarize = mcp_response.get(
            "context", "デフォルトのコンテキスト"
        )  # 仮
        summary = gemini_service.summarize(text_to_summarize)
        logger.info(f"Gemini Summary: {summary}")

        # 4. Slackに通知を送信
        slack_service = SlackService()
        result_message = f"「{user_query}」に関するGeminiによる要約:\n{summary}"
        slack_service.post_to_response_url(slack_response_url, result_message)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "Successfully processed and sent summary via Gemini."}
            ),
        }

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        # エラー発生時もSlackに応答を試みる
        if "slack_response_url" in locals() and slack_response_url:
            try:
                slack_service = SlackService()
                slack_service.post_to_response_url(
                    slack_response_url,
                    f"申し訳ありません、処理中にエラーが発生しました: {str(e)}",
                )
            except Exception as slack_err:
                logger.error(f"Failed to send error to Slack: {slack_err}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Failed to process request: {str(e)}"}),
        }
