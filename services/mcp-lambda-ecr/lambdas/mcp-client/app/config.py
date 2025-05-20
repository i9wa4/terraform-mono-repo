# app/config.py (修正・確認ポイント追記版)
import json
import logging
import os

import boto3

logger = logging.getLogger(__name__)


class AppConfig:
    def __init__(self):
        # --- ▼▼▼ 確認ポイント 1: 環境変数名とシークレット名のマッピング ▼▼▼ ---
        # Lambdaの環境変数からSecrets Managerのシークレット名を取得
        # これらの環境変数が正しく設定されているか、また意図したシークレット名を指しているかご確認ください。
        gemini_api_key_secret_name = os.environ.get("MCP_CLIENT_SECRET_NAME")
        # 注意: slack_webhook_url_secret_name も同じ環境変数 "MCP_CLIENT_SECRET_NAME" を参照しています。
        # もしGemini APIキーとSlack Webhook URLが別々のシークレットに保存されている場合、
        # ここは異なる環境変数名を参照するように変更する必要があります。
        # (例: os.environ.get("SLACK_SECRET_NAME") など)
        slack_webhook_url_secret_name = os.environ.get("MCP_CLIENT_SECRET_NAME")
        mcp_server_url_secret_name = os.environ.get("MCP_SERVER_EXAMPLE_SECRET_NAME")
        # --- ▲▲▲ 確認ポイント 1 ---

        expected_env_vars = {
            "GEMINI_API_KEY_SECRET_NAME (現在は MCP_CLIENT_SECRET_NAME)": (
                gemini_api_key_secret_name
            ),
            "SLACK_WEBHOOK_URL_SECRET_NAME (現在は MCP_CLIENT_SECRET_NAME)": (
                slack_webhook_url_secret_name
            ),
            "MCP_SERVER_URL_SECRET_NAME": mcp_server_url_secret_name,
        }
        missing_vars = [name for name, value in expected_env_vars.items() if not value]

        if missing_vars:
            raise ValueError(
                "Missing environment variables for Secrets Manager names:"
                f" {', '.join(missing_vars)}"
            )

        try:
            session = boto3.session.Session()
            client = session.client(service_name="secretsmanager")

            # --- Gemini API Key の処理 ---
            gemini_secret_response = client.get_secret_value(
                SecretId=gemini_api_key_secret_name
            )
            if "SecretString" in gemini_secret_response:
                gemini_secret_string = gemini_secret_response["SecretString"]
                # --- ▼▼▼ 確認ポイント 2a: シークレット内のキー名 ▼▼▼ ---
                # Secrets Managerの "MCP_CLIENT_SECRET_NAME" (gemini_api_key_secret_name) に保存されている
                # JSON内のGemini APIキーのキー名が "GEMINI_API_KEY" であることを確認してください。
                # もし異なる場合は、ここの文字列を実際のキー名に変更してください。
                self._gemini_api_key = json.loads(gemini_secret_string).get(
                    "GEMINI_API_KEY"
                )
                # --- ▲▲▲ 確認ポイント 2a ---
            else:
                raise ValueError(
                    "SecretString not found for Gemini API Key in"
                    f" {gemini_api_key_secret_name}"
                )
            if not self._gemini_api_key:
                raise ValueError(
                    "GEMINI_API_KEY not found within secret"  # 確認ポイント2aのキー名と合わせる
                    f" {gemini_api_key_secret_name}"
                )

            # --- Slack Webhook URL の処理 ---
            slack_secret_response = client.get_secret_value(
                SecretId=slack_webhook_url_secret_name
            )
            if "SecretString" in slack_secret_response:
                slack_secret_string = slack_secret_response["SecretString"]
                # --- ▼▼▼ 確認ポイント 2b: シークレット内のキー名 ▼▼▼ ---
                # Secrets Managerの "MCP_CLIENT_SECRET_NAME" (slack_webhook_url_secret_name) に保存されている
                # JSON内のSlack Webhook URLのキー名が "SLACK_WEBHOOK_URL" であることを確認してください。
                # もし異なる場合は、ここの文字列を実際のキー名に変更してください。
                self._slack_webhook_url = json.loads(slack_secret_string).get(
                    "SLACK_WEBHOOK_URL"
                )
                # --- ▲▲▲ 確認ポイント 2b ---
            else:
                raise ValueError(
                    "SecretString not found for Slack Webhook URL in"
                    f" {slack_webhook_url_secret_name}"
                )

            # --- ▼▼▼ 確認ポイント 3: Slack Webhook URLの必須性 ▼▼▼ ---
            # Slack Webhook URLがシークレット内に見つからなかった場合の処理です。
            # 現在は警告ログを出し、self._slack_webhook_url に None を設定しています。
            # この挙動が要件に合っているか確認してください。もし必須であればエラーを発生させるべきです。
            if not self._slack_webhook_url:
                logger.warning(
                    "SLACK_WEBHOOK_URL not found within secret %s, but may not be"
                    " required.",  # 確認ポイント2bのキー名と合わせる
                    slack_webhook_url_secret_name,
                )
                self._slack_webhook_url = None
            # --- ▲▲▲ 確認ポイント 3 ---

            # --- MCP Server URL の処理 ---
            mcp_secret_response = client.get_secret_value(
                SecretId=mcp_server_url_secret_name
            )
            if "SecretString" in mcp_secret_response:
                mcp_secret_string = mcp_secret_response["SecretString"]
                # --- ▼▼▼ 確認ポイント 2c: シークレット内のキー名 ▼▼▼ ---
                # Secrets Managerの "MCP_SERVER_EXAMPLE_SECRET_NAME" (mcp_server_url_secret_name) に保存されている
                # JSON内のMCP Server URL (Function URL) のキー名が "FUNCTION_URL" であることを確認してください。
                # もし異なる場合は、ここの文字列を実際のキー名に変更してください。
                self._mcp_server_url = json.loads(mcp_secret_string).get("FUNCTION_URL")
                # --- ▲▲▲ 確認ポイント 2c ---
            else:
                raise ValueError(
                    "SecretString not found for MCP Server URL in"
                    f" {mcp_server_url_secret_name}"
                )
            if not self._mcp_server_url:
                raise ValueError(
                    "FUNCTION_URL not found within secret"  # 確認ポイント2cのキー名と合わせる
                    f" {mcp_server_url_secret_name}"
                )

            logger.info("Successfully loaded secrets from AWS Secrets Manager.")

        except Exception as e:
            logger.error(
                f"Error retrieving secrets from AWS Secrets Manager: {e}", exc_info=True
            )
            raise

    @property
    def gemini_api_key(self) -> str:
        if not hasattr(self, "_gemini_api_key") or not self._gemini_api_key:
            raise ValueError("Gemini API Key is not loaded.")
        return self._gemini_api_key

    @property
    def slack_webhook_url(self) -> str:
        if not hasattr(self, "_slack_webhook_url") or not self._slack_webhook_url:
            logger.warning(
                "Slack Webhook URL is not loaded, but may not be required if using"
                " response_url."
            )
            return None
        return self._slack_webhook_url

    @property
    def mcp_server_url(self) -> str:
        if not hasattr(self, "_mcp_server_url") or not self._mcp_server_url:
            raise ValueError("MCP Server URL is not loaded.")
        return self._mcp_server_url
