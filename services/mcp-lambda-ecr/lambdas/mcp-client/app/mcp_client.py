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

    def __init__(
        self, gemini_api_key: str, mcp_connections: Dict[str, Dict[str, Any]]
    ):
        logger.info(
            "GeminiMCPClient __init__: Initializing with API key and connections."
        )
        self.gemini_api_key = gemini_api_key
        self.mcp_connections = mcp_connections
        logger.info(
            f"GeminiMCPClient __init__: MCP Connections: {self.mcp_connections}"
        )
        self.model = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro", google_api_key=gemini_api_key, temperature=0
        )
        logger.info(
            "GeminiMCPClient __init__: ChatGoogleGenerativeAI model initialized."
        )
        self.client = MultiServerMCPClient(self.mcp_connections)
        logger.info("GeminiMCPClient __init__: MultiServerMCPClient initialized.")
        self.agent = None
        logger.info("GeminiMCPClient __init__: Completed.")

    async def initialize(self):
        """MCPクライアントとエージェントを初期化"""
        logger.info("Initializing MCP client and agent.")
        tools = await self.client.get_tools()
        logger.info(f"Successfully retrieved {len(tools)} tools: {[tool.name for tool in tools]}")

        self.agent = create_react_agent(self.model, tools)

    async def query(self, message: str) -> str:
        """エージェントにクエリを送信"""
        logger.info(f"Querying agent with message: {message}")
        if not self.agent:
            await self.initialize()
            if not self.agent:
                raise RuntimeError(
                    "Agent not initialized even after calling initialize()."
                )

        logger.info("Start agent invocation...")
        final_state = None
        async for log in self.agent.astream_log(
            {"messages": [HumanMessage(content=message)]},
            include_names=["__start__", "__end__"],
        ):
            logger.info(f"Agent stream log: {log}")
            if log.path.endswith("/__end__"):
                final_state = log.data.get("output")

        logger.info("Agent invocation finished.")

        if final_state and "messages" in final_state and final_state["messages"]:
            return final_state["messages"][-1].content

        return "Agent did not return a final answer."

    async def get_available_tools(self) -> List[str]:
        """利用可能なツール一覧を取得"""
        logger.info("Fetching available tools from MCP client.")
        if not self.client:
            self.client = MultiServerMCPClient(self.mcp_connections)

        tools = await self.client.get_tools()
        return [tool.name for tool in tools]

    async def close(self):
        """リソースをクリーンアップ"""
        logger.info("Closing MCP client and cleaning up resources.")
        if self.client:
            pass
