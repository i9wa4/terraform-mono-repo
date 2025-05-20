# app/lambda_function.py
import json
import logging
from urllib.parse import parse_qs  # parse_qs を使う場合はここで import

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
    config = AppConfig()  # グローバル変数として config を定義
except Exception as e:
    logger.critical(f"Failed to initialize AppConfig: {e}", exc_info=True)
    # 設定読み込み失敗時はLambdaの初期化で失敗させる
    raise


def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    # グローバルスコープで初期化された config インスタンスを使用します
    # (ここでの AppConfig() の再初期化は不要)

    try:
        # 1. Slackイベントからユーザーのクエリを抽出 (実際の構造に依存)
        #    ここではSlash Commandのペイロードを想定
        #    Slackからのリクエストボディは通常URLエンコードされているため、パースが必要な場合がある

        # slack_payload の初期化
        slack_payload = {}
        event_body = event.get("body")  # eventからbodyを取得

        if isinstance(event_body, str):
            try:
                # API Gateway経由の場合、bodyが文字列化されたJSONのことがある
                slack_payload = json.loads(event_body)
                logger.info("Parsed event body as JSON.")
            except json.JSONDecodeError:
                # application/x-www-form-urlencoded の場合
                try:
                    parsed_qs_body = parse_qs(event_body)
                    # parse_qs は {'key': ['value']} の形式で返すため、各値の最初の要素を取得
                    # 値が存在しないキーや空のリストの場合は処理をスキップ
                    slack_payload = {
                        k: v[0]
                        for k, v in parsed_qs_body.items()
                        if v and isinstance(v, list) and len(v) > 0
                    }
                    logger.info(
                        "Parsed event body as application/x-www-form-urlencoded."
                    )
                except (
                    Exception
                ) as parse_err:  # parse_qs 自体のエラーや予期せぬ形式の場合
                    logger.error(
                        f"Failed to parse URL encoded body: {parse_err}", exc_info=True
                    )
                    # パースに失敗した場合は slack_payload は空のままか、エラーに応じた処理
                    slack_payload = {}
        elif isinstance(
            event_body, dict
        ):  # bodyが既に辞書の場合 (Lambdaコンソールのテストイベントなど)
            slack_payload = event_body
            logger.info("Event body is already a dictionary.")
        else:  # bodyがない、または予期しない型の場合
            logger.warning(
                f"Event body is missing or not a string/dict: {type(event_body)}."
                " Assuming empty payload."
            )
            slack_payload = {}

        user_query = slack_payload.get("text")
        slack_response_url = slack_payload.get("response_url")

        if not user_query or not slack_response_url:
            logger.error(
                f"Missing user_query or slack_response_url. user_query: '{user_query}',"
                f" slack_response_url: '{slack_response_url}'"
            )
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "text": (
                            "リクエストが無効です。user_query または response_url"
                            " が見つかりません。"
                        )
                    }
                ),
            }

        # 2. MCPサーバーに接続
        #    グローバルな config インスタンスのプロパティを使用
        mcp_service = MCPService(config.mcp_server_url)
        mcp_response = mcp_service.ask(user_query)
        logger.info(f"MCP Server Response: {mcp_response}")

        # 3. Gemini APIから要約を取得
        #    グローバルな config インスタンスのプロパティを使用
        gemini_service = GeminiService(config.gemini_api_key)

        # mcp_responseから要約対象のテキストを抽出するロジック
        # キー名 'context' が存在しない場合も考慮
        text_to_summarize = mcp_response.get("context")
        if not text_to_summarize:
            logger.warning(
                "MCP Server response did not contain 'context'. Using user_query for"
                " summary."
            )
            text_to_summarize = (
                user_query  # フォールバックとして元のクエリを使うか、エラーにするか検討
            )

        summary = gemini_service.summarize(text_to_summarize)
        logger.info(f"Gemini Summary: {summary}")

        # 4. Slackに通知を送信
        #    SlackService の初期化時に config.slack_webhook_url を渡すか、
        #    または post_to_response_url のみを使用する場合は引数不要のままにするか、
        #    SlackService の設計によります。現在の SlackService は __init__ で webhook_url を
        #    オプショナルで受け取るようになっているため、ここでは引数なしで初期化します。
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
        # slack_response_url がこのスコープで定義されているか確認
        # (user_queryやslack_response_urlのチェックより前でエラーが発生した場合を考慮)
        current_slack_response_url = None
        if "slack_payload" in locals() and isinstance(slack_payload, dict):
            current_slack_response_url = slack_payload.get("response_url")
        elif (
            "slack_response_url" in locals()
        ):  # if not user_query or not slack_response_url: の後で定義されている場合
            current_slack_response_url = slack_response_url

        if current_slack_response_url:
            try:
                # SlackService のインスタンス化 (エラーハンドリング用)
                # もし既に slack_service が初期化されていればそれを使う
                if "slack_service" not in locals():
                    slack_service = SlackService()

                error_message_to_slack = (
                    f"申し訳ありません、処理中にエラーが発生しました。"
                )
                # デバッグ用にエラー詳細を含める場合は注意（ユーザーに見せるべき情報か）
                # error_message_to_slack += f"\nDetails: {str(e)}"

                slack_service.post_to_response_url(
                    current_slack_response_url, error_message_to_slack
                )
            except Exception as slack_err:
                logger.error(
                    f"Failed to send error to Slack: {slack_err}", exc_info=True
                )

        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Failed to process request: {str(e)}"}),
        }
