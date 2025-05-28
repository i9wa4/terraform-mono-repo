import logging
from typing import Any
from typing import Dict
from typing import List

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GeminiMCPClient:
    """Gemini APIを使用して複数のMCPサーバーに接続するクライアント"""

    def __init__(self, gemini_api_key: str, mcp_connections: Dict[str, Dict[str, Any]]):
        logger.info(
            "Initializing GeminiMCPClient with provided API key and connections."
        )
        self.gemini_api_key = gemini_api_key
        self.mcp_connections = mcp_connections
        self.model = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro", google_api_key=gemini_api_key, temperature=0
        )
        # MultiServerMCPClient のインスタンスをここで作成
        self.client = MultiServerMCPClient(self.mcp_connections)
        self.agent = None

    async def initialize(self):
        """MCPクライアントとエージェントを初期化"""
        logger.info("Initializing MCP client and agent.")
        # README の例に従い、インスタンスから直接 get_tools() を呼び出す
        tools = await self.client.get_tools()

        # Geminiモデルでエージェントを作成
        self.agent = create_react_agent(self.model, tools)

    async def query(self, message: str) -> str:
        """エージェントにクエリを送信"""
        logger.info(f"Querying agent with message: {message}")
        if not self.agent:
            # initialize が呼ばれていない場合は agent が None の可能性があるため
            await self.initialize()
            if not self.agent:  # それでも None ならエラー
                raise RuntimeError(
                    "Agent not initialized even after calling initialize()."
                )

        response = await self.agent.ainvoke(
            {"messages": [HumanMessage(content=message)]}
        )

        return response["messages"][-1].content

    async def get_available_tools(self) -> List[str]:
        """利用可能なツール一覧を取得"""
        logger.info("Fetching available tools from MCP client.")
        if not self.client:
            # client が __init__ で作成されるが、念のため
            self.client = MultiServerMCPClient(self.mcp_connections)

        tools = await self.client.get_tools()
        return [tool.name for tool in tools]

    async def close(self):
        """リソースをクリーンアップ"""
        logger.info("Closing MCP client and cleaning up resources.")
        if self.client:
            # 例: もし client に aclose() のようなメソッドがあれば呼び出す
            # if hasattr(self.client, 'aclose'):
            #     await self.client.aclose()
            pass
