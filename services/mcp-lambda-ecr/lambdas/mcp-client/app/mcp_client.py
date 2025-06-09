import logging
from typing import Any, Dict, List

from app.boto_mcp_transport import BotoMCPTransport
from langchain_core.messages import HumanMessage
from langchain_core.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GeminiMCPClient:
    """boto3経由で単一のMCPサーバーに接続し、Geminiエージェントを操作するクライアント"""

    def __init__(
        self,
        gemini_api_key: str,
        server_function_name: str,
        server_api_key: str | None = None,
    ):
        logger.info(
            f"GeminiMCPClient __init__: Initializing for server"
            f" '{server_function_name}'."
        )
        self.model = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro", google_api_key=gemini_api_key, temperature=0
        )
        self.transport = BotoMCPTransport(
            function_name=server_function_name, api_key=server_api_key
        )
        self.agent = None
        logger.info("GeminiMCPClient __init__: Completed.")

    async def initialize(self):
        """非同期でツールを取得し、エージェントを初期化する"""
        logger.info("Initializing agent by fetching remote tools...")
        tools = []
        async for tool_response in self.transport.get_tools_stream():
            if tool_response.get("result", {}).get("tools"):
                tool_definitions = tool_response["result"]["tools"]
                logger.info(f"Received {len(tool_definitions)} tool definitions.")

                for definition in tool_definitions:
                    tool_name = definition.get("function", {}).get("name")
                    if not tool_name:
                        logger.warning(f"Skipping tool with no name: {definition}")
                        continue

                    def create_tool_coroutine(
                        name: str, transport: BotoMCPTransport
                    ):
                        """非同期ツール実行関数を生成するファクトリ"""

                        async def _tool_executor(**kwargs):
                            mcp_tool_call = {
                                "jsonrpc": "2.0",
                                "method": name,
                                "params": kwargs,
                                "id": "1",
                            }
                            logger.info(f"Invoking tool '{name}' with params: {kwargs}")
                            response = await transport.invoke_tool(mcp_tool_call)
                            logger.info(
                                f"Received response for tool '{name}': {response}"
                            )
                            return response.get("result")

                        return _tool_executor

                    new_tool = Tool(
                        name=tool_name,
                        description=definition.get("function", {}).get("description"),
                        coroutine=create_tool_coroutine(tool_name, self.transport),
                    )
                    tools.append(new_tool)

        logger.info(
            f"Successfully created {len(tools)} tools: {[tool.name for tool in tools]}"
        )
        self.agent = create_react_agent(self.model, tools)

    async def query(self, message: str) -> str:
        """エージェントにクエリを送信し、中間ログを出力する"""
        logger.info(f"Querying agent with message: {message}")
        if not self.agent:
            await self.initialize()
            if not self.agent:
                raise RuntimeError("Agent not initialized.")

        logger.info("Start agent invocation...")
        final_state = None
        async for log in self.agent.astream_log(
            {"messages": [HumanMessage(content=message)]}
        ):
            logger.info(f"Agent stream log: {log}")
            if log.path.endswith("/__end__"):
                final_state = log.data.get("output")

        logger.info("Agent invocation finished.")

        if final_state and "messages" in final_state and final_state["messages"]:
            return final_state["messages"][-1].content

        return "Agent did not return a final answer."

    async def close(self):
        """リソースをクリーンアップ"""
        logger.info("Closing client and cleaning up resources.")
        pass
