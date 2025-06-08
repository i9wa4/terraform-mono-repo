import importlib
import json
import logging
import os

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_target_mcp_object():
    """環境変数に基づいて、ラップ対象のMCPオブジェクトを動的にインポートする"""
    module_path = os.environ.get("MCP_MODULE_PATH")  # 例: "mcp_databricks_server.main"
    object_name = os.environ.get("MCP_OBJECT_NAME")  # 例: "mcp"

    if not module_path or not object_name:
        raise ValueError(
            "MCP_MODULE_PATH and MCP_OBJECT_NAME environment variables must be set."
        )

    try:
        module = importlib.import_module(module_path)
        mcp_object = getattr(module, object_name)
        logger.info(f"Successfully imported '{object_name}' from '{module_path}'.")
        return mcp_object
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to dynamically import MCP object: {e}")
        raise


def create_app(auth_api_key: str | None) -> FastAPI:
    """汎用的なFastAPIラッパーアプリケーションを生成する"""
    app = FastAPI(
        title="Generic MCP Server Wrapper",
        description="A generic wrapper to host Python-based MCP servers on AWS Lambda.",
        version="2.0.0",
    )

    # ラップ対象のMCPオブジェクトを動的に取得
    target_mcp_object = get_target_mcp_object()

    # MCPオブジェクトからツール定義とディスパッチテーブルを動的に生成
    tool_definitions = [tool.schema for tool in target_mcp_object.tools]
    dispatch_table = {tool.name: tool.func for tool in target_mcp_object.tools}
    logger.info(
        f"Loaded {len(tool_definitions)} tools:"
        f" {[name for name in dispatch_table.keys()]}"
    )

    # APIキー認証 (変更なし)
    api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)

    async def api_key_auth(api_key: str = Depends(api_key_header)):
        if auth_api_key and api_key != auth_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
            )
        return api_key

    @app.route("/mcp", methods=["GET", "POST"])
    async def mcp_endpoint(request: Request, _=Depends(api_key_auth)):
        # GETリクエストの処理
        if request.method == "GET":

            async def tool_list_generator():
                response = {
                    "jsonrpc": "2.0",
                    "id": "0",
                    "result": {"tools": tool_definitions},
                }
                yield f"data: {json.dumps(response)}\n\n"

            return StreamingResponse(
                tool_list_generator(), media_type="text/event-stream"
            )

        # POSTリクエストの処理
        if request.method == "POST":
            body = await request.json()
            tool_name = body.get("method")
            params = body.get("params", {})
            request_id = body.get("id", "1")

            tool_func = dispatch_table.get(tool_name)
            if not tool_func:
                raise HTTPException(
                    status_code=404, detail=f"Tool '{tool_name}' not found."
                )

            try:
                result = await tool_func(**params)
                return JSONResponse(
                    content={"jsonrpc": "2.0", "id": request_id, "result": result}
                )
            except Exception as e:
                logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
                return JSONResponse(
                    status_code=500,
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": "Internal server error",
                            "data": str(e),
                        },
                    },
                )

    return app
