# app/lambda_function.py
import json
import logging
from urllib.parse import parse_qs  # parse_qs を使う場合はここで import

from app.config import AppConfig
from app.gemini_service import GeminiService
from app.mcp_service import MCPService
from app.slack_service import SlackService

logger = logging.getLogger()
logger.setLevel(logging.INFO)  # ログレベルをINFOに設定

# AppConfigのインスタンスはLambdaのグローバルスコープで初期化
try:
    config = AppConfig()
    logger.info("AppConfig initialized globally.")
except Exception as e:
    logger.critical(
        f"CRITICAL - Failed to initialize AppConfig globally: {e}", exc_info=True
    )
    # 設定読み込み失敗時はLambdaの初期化で失敗させることで、コールドスタート時に問題を検知
    raise


def lambda_handler(event, context):
    # リクエストIDをログに含めると追跡しやすくなります
    request_id = context.aws_request_id if context else "N/A"
    logger.info(f"Request ID: {request_id} - Received event: {json.dumps(event)}")

    # グローバルスコープで初期化された config インスタンスを使用します
    # try-except は AppConfig の初期化ではなく、ハンドラ全体の処理を囲む形にします

    # slack_payload と slack_response_url を早い段階で初期化
    slack_payload = {}
    slack_response_url = None  # エラーハンドリングで参照できるように先にNoneで定義

    try:
        # 1. Slackイベントからユーザーのクエリを抽出
        event_body = event.get("body")

        if isinstance(event_body, str):
            try:
                slack_payload = json.loads(event_body)
                logger.info(f"Request ID: {request_id} - Parsed event body as JSON.")
            except json.JSONDecodeError:
                try:
                    parsed_qs_body = parse_qs(event_body)
                    slack_payload = {
                        k: v[0]
                        for k, v in parsed_qs_body.items()
                        if v and isinstance(v, list) and len(v) > 0
                    }
                    logger.info(
                        f"Request ID: {request_id} - Parsed event body as"
                        " application/x-www-form-urlencoded."
                    )
                except Exception as parse_err:
                    logger.error(
                        f"Request ID: {request_id} - Failed to parse URL encoded body:"
                        f" {parse_err}",
                        exc_info=True,
                    )
                    slack_payload = {}
        elif isinstance(event_body, dict):
            slack_payload = event_body
            logger.info(
                f"Request ID: {request_id} - Event body is already a dictionary."
            )
        else:
            logger.warning(
                f"Request ID: {request_id} - Event body is missing or not a"
                f" string/dict: {type(event_body)}. Assuming empty payload."
            )
            slack_payload = {}

        user_query = slack_payload.get("text")
        slack_response_url = slack_payload.get("response_url")  # ここで代入

        if not user_query or not slack_response_url:
            error_message = (
                f"Missing user_query or slack_response_url. user_query: '{user_query}',"
                f" slack_response_url: '{slack_response_url}'"
            )
            logger.error(f"Request ID: {request_id} - {error_message}")
            return {
                "statusCode": 400,
                # Slackに返す場合はSlackが期待する形式でエラーメッセージを返すのが親切
                "body": json.dumps(
                    {
                        "response_type": "ephemeral",
                        "text": f"リクエストが無効です: {error_message}",
                    }
                ),
                "headers": {"Content-Type": "application/json"},
            }

        logger.info(
            f"Request ID: {request_id} - User Query: '{user_query}', Slack Response"
            f" URL: '{slack_response_url}'"
        )

        # 2. MCPサーバーに接続
        mcp_service = MCPService(config.mcp_server_url)
        mcp_response = mcp_service.ask(user_query)
        logger.info(f"Request ID: {request_id} - MCP Server Response: {mcp_response}")

        # 3. Gemini APIから要約を取得
        gemini_service = GeminiService(config.gemini_api_key)

        text_to_summarize = mcp_response.get(
            "context"
        )  # mcp_server-example のレスポンスキーに合わせる
        if not text_to_summarize:
            logger.warning(
                f"Request ID: {request_id} - MCP Server response did not contain"
                " 'context'. Using original user_query for summary."
            )
            text_to_summarize = user_query

        summary = gemini_service.summarize(text_to_summarize)
        logger.info(f"Request ID: {request_id} - Gemini Summary: {summary}")

        # 4. Slackに通知を送信
        slack_service = SlackService()  # config.slack_webhook_url はここでは使わない
        result_message = f"「{user_query}」に関するGeminiによる要約:\n{summary}"
        slack_service.post_to_response_url(slack_response_url, result_message)
        logger.info(
            f"Request ID: {request_id} - Successfully posted summary to Slack"
            " response_url."
        )

        # SlackのSlash Commandに対する即時応答は、通常はステータスコード200で空のボディか、
        # "コマンドを受け付けました" のような短いメッセージです。
        # 実際の処理結果は response_url を使って非同期に送信します。
        # ここでは、呼び出し元（API Gatewayなど）への成功応答を返します。
        return {
            "statusCode": 200,
            "body": json.dumps(  # API GatewayがこのLambdaを直接呼び出す場合、空のボディかシンプルなメッセージが良い
                # Slackに返すメッセージは response_url 経由なので、ここは何でもよい
                {"message": "Processing started. Result will be sent to Slack."}
            ),
            "headers": {"Content-Type": "application/json"},
        }

    except Exception as e:
        # リクエストIDをエラーログに含める
        logger.error(
            f"Request ID: {request_id} - Error processing request: {e}", exc_info=True
        )

        # エラー発生時もSlackに応答を試みる
        # slack_response_url は try ブロックの最初の方で取得・設定されているはず
        if slack_response_url:
            try:
                # SlackService のインスタンス化 (エラーハンドリング用)
                # もし try ブロック内で既に slack_service が初期化されていればそれを使う
                # (現状のコードでは try ブロックの後半で初期化されるので、ここで再度初期化が必要な場合がある)
                if "slack_service" not in locals() or not isinstance(
                    slack_service, SlackService
                ):
                    slack_service_for_error = SlackService()
                else:  # tryブロックで既に作られていたらそれを使う
                    slack_service_for_error = slack_service

                error_message_to_slack = (
                    f"申し訳ありません、リクエストの処理中にエラーが発生しました。"
                )
                # デバッグ情報を含めたい場合は、ユーザーに見せても安全な情報のみにする
                # error_message_to_slack += f"\nRequest ID: {request_id}"

                slack_service_for_error.post_to_response_url(
                    slack_response_url, error_message_to_slack
                )
                logger.info(
                    f"Request ID: {request_id} - Sent error message to Slack"
                    " response_url."
                )
            except Exception as slack_err:
                logger.error(
                    f"Request ID: {request_id} - Failed to send error to Slack:"
                    f" {slack_err}",
                    exc_info=True,
                )
        else:
            logger.warning(
                f"Request ID: {request_id} - slack_response_url not available to send"
                " error message to Slack."
            )

        return {
            "statusCode": 500,
            "body": json.dumps(
                {"error": f"Failed to process request. Request ID: {request_id}"}
            ),
            "headers": {"Content-Type": "application/json"},
        }
