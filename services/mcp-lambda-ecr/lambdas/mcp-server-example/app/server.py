import asyncio
import logging
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from fastapi.responses import StreamingResponse
from langchain_community.tools import GoogleSearchAPIWrapper
from mcp.protocol import Message, Tool
from langchain_core.tools import tool as ToolDecorator

logger = logging.getLogger(__name__)


def create_app(auth_api_key: str | None) -> FastAPI:
    """
    FastAPIアプリケーションのインスタンスを生成して返すファクトリ関数。

    この関数がサーバー実装の本体となる。
    認証キーやツールの定義、エンドポイントのルーティングはすべてここで行う。

    Args:
        auth_api_key (str | None): APIキー認証に使用するキー。Noneの場合は認証を無効化。

    Returns:
        FastAPI: 設定済みのFastAPIアプリケーションインスタンス。
    """
    app = FastAPI(
        title="MCP Server Example",
        description="An example server for the Multi-Tool Calling Protocol (MCP).",
        version="1.0.0",
    )

    # --- Tool Definition ---
    Google Search_wrapper = GoogleSearchAPIWrapper()

    @ToolDecorator
    def Google Search(query: str) -> str:
        """Searches Google and returns the results."""
        return Google Search_wrapper.run(query)

    tools = [Google Search]
    tool_definitions = [
        Tool(name=t.name, description=t.description, input_schema=t.args)
        for t in tools
    ]

    # --- Authentication ---
    api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)

    async def api_key_auth(api_key: str = Depends(api_key_header)):
        # 認証キーが設定されており、かつリクエストのキーが一致しない場合のみエラー
        if auth_api_key and api_key != auth_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key",
            )
        return api_key

    # --- Endpoints ---
    @app.get("/")
    def read_root():
        return {"message": "MCP Server Example is running."}

    @app.route("/mcp", methods=["GET", "POST"])
    async def mcp_endpoint(request: Request, _=Depends(api_key_auth)):
        # GET: SSE接続の開始とツールリストの送信
        if request.method == "GET":
            async def tool_list_generator():
                list_tools_response = Message(
                    id="0",
                    type="response",
                    payload={"result": [t.model_dump() for t in tool_definitions]},
                )
                yield f"data: {list_tools_response.model_dump_json()}\n\n"
                while True:
                    await asyncio.sleep(30)
                    yield ": keep-alive\n\n"

            return StreamingResponse(tool_list_generator(), media_type="text/event-stream")

        # POST: ツール実行（この例では未実装）
        if request.method == "POST":
             raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Tool execution is not implemented in this example."
            )

        raise HTTPException(status_code=405, detail="Method Not Allowed")

    return app
