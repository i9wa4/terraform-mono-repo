import asyncio
import logging

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from mcp.protocol import Message
from mcp.protocol import Tool

# from langchain_core.tools import tool as ToolDecorator # toolデコレータも不要に

logger = logging.getLogger(__name__)


def create_app(auth_api_key: str | None) -> FastAPI:
    """
    FastAPIアプリケーションのインスタンスを生成して返すファクトリ関数。
    """
    app = FastAPI(
        title="MCP Server Example",
        description="An example server for the Multi-Tool Calling Protocol (MCP).",
        version="1.0.0",
    )

    # --- Tool Definition ---
    # ツールを定義しないので、このセクションは空にする
    tools = []
    tool_definitions = []

    # --- Authentication ---
    api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)

    async def api_key_auth(api_key: str = Depends(api_key_header)):
        if auth_api_key and api_key != auth_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key",
            )
        return api_key

    # --- Endpoints ---
    @app.get("/")
    def read_root():
        return {"message": "MCP Server Example is running (no tools configured)."}

    @app.route("/mcp", methods=["GET", "POST"])
    async def mcp_endpoint(request: Request, _=Depends(api_key_auth)):
        # GET: SSE接続の開始とツールリストの送信 (リストは空)
        if request.method == "GET":

            async def tool_list_generator():
                list_tools_response = Message(
                    id="0",
                    type="response",
                    payload={
                        "result": [t.model_dump() for t in tool_definitions]
                    },  # tool_definitions は空
                )
                yield f"data: {list_tools_response.model_dump_json()}\n\n"
                while True:
                    await asyncio.sleep(30)
                    yield ": keep-alive\n\n"

            return StreamingResponse(
                tool_list_generator(), media_type="text/event-stream"
            )

        # POST: ツール実行
        if request.method == "POST":
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Tool execution is not implemented in this example.",
            )

        raise HTTPException(status_code=405, detail="Method Not Allowed")

    return app
