# app/mcp_service.py
import json  # payload をjson文字列にするため
import logging
import os

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.exceptions import NoCredentialsError
from botocore.exceptions import PartialCredentialsError

logger = logging.getLogger(__name__)


class MCPService:
    def __init__(self, server_url: str):
        self.server_url = server_url
        if not self.server_url:
            logger.error("MCPService initialized with no server_url.")
            raise ValueError("MCP Server URL is not configured.")

        try:
            self.session = boto3.Session()
            # Lambda実行ロールの一時認証情報を取得
            self.credentials = self.session.get_credentials()
            if self.credentials is None:
                logger.error("Failed to get AWS credentials from session.")
                raise ValueError("AWS credentials could not be loaded from session.")

            self.frozen_credentials = self.credentials.get_frozen_credentials()
            if self.frozen_credentials is None:
                logger.error("Failed to get frozen AWS credentials.")
                raise ValueError("Frozen AWS credentials could not be obtained.")

            # Lambdaの環境変数 'AWS_REGION' からリージョンを取得
            self.aws_region = os.environ.get("AWS_REGION")
            if not self.aws_region:
                # セッションからリージョンを取得するフォールバック
                self.aws_region = self.session.region_name
                if not self.aws_region:
                    logger.error(
                        "AWS Region could not be determined. Ensure AWS_REGION"
                        " environment variable is set or Lambda is configured with a"
                        " region."
                    )
                    raise ValueError("AWS Region could not be determined.")

            logger.info(
                f"MCPService initialized for URL: {self.server_url} in region:"
                f" {self.aws_region}"
            )

        except (NoCredentialsError, PartialCredentialsError) as e:
            logger.error(
                f"Error loading AWS credentials for MCPService: {e}", exc_info=True
            )
            raise ValueError(f"Error loading AWS credentials for MCPService: {e}")
        except Exception as e:  # その他のboto3初期化エラー
            logger.error(f"Error initializing MCPService for SigV4: {e}", exc_info=True)
            raise

    def ask(self, query: str) -> dict:
        url = self.server_url
        # ターゲットLambda (mcp-server-example) が期待するペイロード形式
        # mcp-server-example/app/lambda_function.py を見ると、{"query": "ユーザーの質問"} を期待
        payload = {"query": query}
        logger.info(
            f"Sending query to MCP Server: {url} with payload: {json.dumps(payload)}"
        )

        try:
            aws_request = AWSRequest(
                method="POST",  # ターゲットLambdaのHTTPメソッド
                url=url,
                data=json.dumps(payload),  # ペイロードをJSON文字列にする
                headers={"Content-Type": "application/json"},
            )

            # SigV4署名を追加 (サービス名は 'lambda')
            SigV4Auth(self.frozen_credentials, "lambda", self.aws_region).add_auth(
                aws_request
            )

            prepped_request = aws_request.prepare()
            logger.debug(f"Prepared MCP request headers: {prepped_request.headers}")
            logger.debug(f"Prepared MCP request body: {prepped_request.body}")

            response = requests.request(
                method=prepped_request.method,
                url=prepped_request.url,
                headers=prepped_request.headers,
                data=prepped_request.body,
                timeout=20,  # タイムアウトを少し長めに設定 (例: 20秒)
            )
            logger.info(f"MCP Server Response Status: {response.status_code}")
            response.raise_for_status()  # HTTPエラーステータスコードの場合、例外を発生
            return response.json()  # レスポンスがJSONの場合

        except requests.exceptions.HTTPError as e:
            error_content = (
                e.response.text if e.response is not None else "No response content"
            )
            logger.error(
                "HTTPError from MCP server:"
                f" {e.response.status_code if e.response is not None else 'N/A'} -"
                f" {error_content}",
                exc_info=True,
            )
            raise ConnectionError(
                f"Failed to get response from MCP server: {str(e)}"
            ) from e
        except requests.exceptions.Timeout:
            logger.error(f"Timeout connecting to MCP server: {url}", exc_info=True)
            raise ConnectionError(f"Timeout connecting to MCP server: {url}")
        except Exception as e:
            logger.error(f"General error connecting to MCP server: {e}", exc_info=True)
            raise ConnectionError(f"Failed to connect to MCP server: {str(e)}") from e
