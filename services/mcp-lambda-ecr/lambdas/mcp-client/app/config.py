# app/config.py
import os

from dotenv import load_dotenv  # ローカル開発用

# .envファイルから環境変数を読み込む (ローカル開発時のみ)
# Lambda環境では、環境変数はLambda関数の設定から読み込まれる
load_dotenv()


class AppConfig:
    def __init__(self):
        self.mcp_server_url = os.environ.get("MCP_SERVER_URL")
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")  #

        if not self.mcp_server_url:
            raise ValueError("MCP_SERVER_URL environment variable is not set.")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")
