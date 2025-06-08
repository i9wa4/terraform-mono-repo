import json
import logging

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader

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

    tool_definitions = []

    api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)

    async def api_key_auth(api_key: str = Depends(api_key_header)):
        if auth_api_key and api_key != auth_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key",
            )
        return api_key

    @app.get("/")
    def read_root():
        return {"message": "MCP Server Example is running (no tools configured)."}

    @app.route("/mcp", methods=["GET", "POST"])
    async def mcp_endpoint(request: Request, _=Depends(api_key_auth)):
        if request.method == "GET":

            async def tool_list_generator():
                # Messageクラスの代わりにdictを使用
                list_tools_response = {
                    "id": "0",
                    "type": "response",
                    "payload": {"result": tool_definitions},
                }
                # model_dump_json()の代わりにjson.dumpsを使用
                yield f"data: {json.dumps(list_tools_response)}\n\n"

                # --- 修正箇所：不要な無限ループとsleepを削除 ---
                # while True:
                #     await asyncio.sleep(30)
                #     yield ": keep-alive\n\n"

            return StreamingResponse(
                tool_list_generator(), media_type="text/event-stream"
            )

        if request.method == "POST":
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Tool execution is not implemented in this example.",
            )

        raise HTTPException(status_code=405, detail="Method Not Allowed")

    return app
