import logging
import sys

from fastmcp import FastMCP

# ロガーの設定
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# FastMCPサーバーの作成
mcp = FastMCP("Simple MCP Demo")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together"""
    logger.info(f"add() tool called: a={a}, b={b}")
    result = a + b
    logger.info(f"add() result: {result}")
    return result


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    logger.info(f"multiply() tool called: a={a}, b={b}")
    result = a * b
    logger.info(f"multiply() result: {result}")
    return result


@mcp.resource("server://status")
def get_server_status() -> str:
    """Get the current server status"""
    logger.info("get_server_status() resource called")
    status = {"status": "running", "version": "1.0.0", "uptime": "N/A"}
    logger.info(f"get_server_status() result: {status}")
    return str(status)


if __name__ == "__main__":
    logger.info("Starting MCP server in SSE mode...")
    mcp.run(transport="sse")
