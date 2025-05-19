# app/mcp_service.py
import logging

import requests

logger = logging.getLogger(__name__)


class MCPService:
    def __init__(self, server_url: str):
        self.server_url = server_url

    def ask(self, query: str) -> dict:
        try:
            # MCPサーバーのAPI仕様に応じてリクエストボディ/パラメータを調整
            response = requests.post(
                self.server_url, json={"query": query}, timeout=10
            )  #
            response.raise_for_status()  # エラーがあればHTTPErrorを発生させる
            logger.info(f"MCP Server Response Status: {response.status_code}")
            return response.json()  # サーバーがJSONを返すと仮定
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to MCP server: {e}", exc_info=True)
            raise ConnectionError(f"Failed to get response from MCP server: {str(e)}")
