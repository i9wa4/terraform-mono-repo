from typing import Any
from typing import Dict
from typing import List

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent


class GeminiMCPClient:
    """Gemini APIを使用して複数のMCPサーバーに接続するクライアント"""

    def __init__(self, gemini_api_key: str, mcp_connections: Dict[str, Dict[str, Any]]):
        """
        Args:
            gemini_api_key: Gemini APIキー
            mcp_connections: MCPサーバー接続設定
        """
        self.gemini_api_key = gemini_api_key
        self.mcp_connections = mcp_connections
        self.model = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro", google_api_key=gemini_api_key, temperature=0
        )
        self.client = None
        self.agent = None

    async def initialize(self):
        """MCPクライアントとエージェントを初期化"""
        self.client = MultiServerMCPClient(self.mcp_connections)
        await self.client.__aenter__()

        # 全てのMCPツールを取得
        tools = self.client.get_tools()

        # Geminiモデルでエージェントを作成
        self.agent = create_react_agent(self.model, tools)

    async def query(self, message: str) -> str:
        """エージェントにクエリを送信"""
        if not self.agent:
            raise RuntimeError("Client not initialized. Call initialize() first.")

        response = await self.agent.ainvoke(
            {"messages": [HumanMessage(content=message)]}
        )

        return response["messages"][-1].content

    async def get_available_tools(self) -> List[str]:
        """利用可能なツール一覧を取得"""
        if not self.client:
            raise RuntimeError("Client not initialized. Call initialize() first.")

        tools = self.client.get_tools()
        return [tool.name for tool in tools]

    async def get_server_tools(self, server_name: str) -> List[str]:
        """特定のサーバーのツール一覧を取得"""
        if not self.client:
            raise RuntimeError("Client not initialized. Call initialize() first.")

        server_tools = self.client.server_name_to_tools.get(server_name, [])
        return [tool.name for tool in server_tools]

    async def close(self):
        """リソースをクリーンアップ"""
        if self.client:
            await self.client.__aexit__(None, None, None)
