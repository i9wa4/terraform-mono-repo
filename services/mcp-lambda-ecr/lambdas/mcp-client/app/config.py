# app/config.py
import json
import logging
import os

import boto3

logger = logging.getLogger(__name__)


class AppConfig:
    def __init__(self):
        gemini_api_key_secret_name = os.environ.get("MCP_CLIENT_SECRET_NAME")
        slack_webhook_url_secret_name = os.environ.get("MCP_CLIENT_SECRET_NAME")
        mcp_server_url_secret_name = os.environ.get("MCP_SERVER_EXAMPLE_SECRET_NAME")

        # 環境変数とその期待される名前のペア
        expected_env_vars = {
            "GEMINI_API_KEY_SECRET_NAME": gemini_api_key_secret_name,
            "SLACK_WEBHOOK_URL_SECRET_NAME": slack_webhook_url_secret_name,
            "MCP_SERVER_URL_SECRET_NAME": mcp_server_url_secret_name,
        }
        # 設定されていない環境変数名をリストアップ
        missing_vars = [name for name, value in expected_env_vars.items() if not value]

        if missing_vars:  # missing_vars リストが空でなければ、何かが不足している
            raise ValueError(
                "Missing environment variables for Secrets Manager names:"
                f" {', '.join(missing_vars)}"
            )

        try:
            session = boto3.session.Session()
            client = session.client(service_name="secretsmanager")

            gemini_secret_value = client.get_secret_value(
                SecretId=gemini_api_key_secret_name
            )
            if "SecretString" in gemini_secret_value:
                self._gemini_api_key = json.loads(gemini_secret_value).get(
                    "GEMINI_API_KEY"
                )
            else:
                raise ValueError(
                    "SecretString not found for Gemini API Key in"
                    f" {gemini_api_key_secret_name}"
                )
            if not self._gemini_api_key:
                raise ValueError(
                    "GEMINI_API_KEY not found within secret"
                    f" {gemini_api_key_secret_name}"
                )

            slack_secret_value = client.get_secret_value(
                SecretId=slack_webhook_url_secret_name
            )
            if "SecretString" in slack_secret_value:
                self._slack_webhook_url = json.loads(slack_secret_value).get(
                    "SLACK_WEBHOOK_URL"
                )
            else:
                raise ValueError(
                    "SecretString not found for Slack Webhook URL in"
                    f" {slack_webhook_url_secret_name}"
                )
            if not self._slack_webhook_url:
                raise ValueError(
                    "SLACK_WEBHOOK_URL not found within secret"
                    f" {slack_webhook_url_secret_name}"
                )

            mcp_secret_value = client.get_secret_value(
                SecretId=mcp_server_url_secret_name
            )
            if "SecretString" in mcp_secret_value:
                self._mcp_server_url = json.loads(mcp_secret_value).get(
                    "FUNCTION_URL"
                )
            else:
                raise ValueError(
                    "SecretString not found for MCP Server URL in"
                    f" {mcp_server_url_secret_name}"
                )
            if not self._mcp_server_url:
                raise ValueError(
                    "MCP_SERVER_URL not found within secret"
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
            # response_url を使う場合は Webhook URL は必須ではないため、エラーにしないことも検討
            logger.warning(
                "Slack Webhook URL is not loaded, but may not be required if using"
                " response_url."
            )
            return None  # または空文字など、利用側で適切に扱える値を返す
        return self._slack_webhook_url

    @property
    def mcp_server_url(self) -> str:
        if not hasattr(self, "_mcp_server_url") or not self._mcp_server_url:
            raise ValueError("MCP Server URL is not loaded.")
        return self._mcp_server_url
