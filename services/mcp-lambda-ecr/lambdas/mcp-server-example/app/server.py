import json
import logging

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader

# mcp-databricks-serverから、ツールとして公開されている個々の関数を直接インポートします
try:
    from mcp_databricks_server.main import describe_table
    from mcp_databricks_server.main import execute_sql_query
    from mcp_databricks_server.main import list_schemas
    from mcp_databricks_server.main import list_tables

    logging.info("Successfully imported tool functions from mcp_databricks_server.main")
except ImportError as e:
    logging.error(f"Could not import tool functions: {e}. Check PYTHONPATH.")
    # エラー時にはNoneを設定し、起動時に検知できるようにします
    execute_sql_query = list_schemas = list_tables = describe_table = None

logger = logging.getLogger(__name__)

# クライアント(Agent)に提示するツール定義リストを、ラッパー側で明示的に記述します
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "execute_sql_query",
            "description": "Execute a SQL query on Databricks and return the results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SQL query to execute.",
                    }
                },
                "required": ["sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_schemas",
            "description": (
                "List all available schemas in a specific catalog on Databricks."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "catalog": {
                        "type": "string",
                        "description": "The name of the catalog.",
                    }
                },
                "required": ["catalog"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "List all tables in a specific schema on Databricks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schema": {
                        "type": "string",
                        "description": (
                            "The name of the schema (e.g., 'catalog_name.schema_name')."
                        ),
                    }
                },
                "required": ["schema"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "describe_table",
            "description": "Describe a table's schema on Databricks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": (
                            "The full name of the table (e.g., 'catalog.schema.table')."
                        ),
                    }
                },
                "required": ["table_name"],
            },
        },
    },
]


def create_app(auth_api_key: str | None) -> FastAPI:
    """FastAPIラッパーアプリケーションを生成するファクトリ関数"""
    app = FastAPI(
        title="Databricks MCP Server Wrapper",
        description="A wrapper for mcp-databricks-server running on AWS Lambda.",
        version="1.0.0",
    )

    if not all([execute_sql_query, list_schemas, list_tables, describe_table]):
        raise RuntimeError(
            "One or more tool functions could not be imported from"
            " mcp_databricks_server."
        )

    # ツール名とインポートした関数を紐付けるディスパッチテーブル（呼び出し辞書）
    dispatch_table = {
        "execute_sql_query": execute_sql_query,
        "list_schemas": list_schemas,
        "list_tables": list_tables,
        "describe_table": describe_table,
    }

    # APIキー認証の仕組み
    api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)

    async def api_key_auth(api_key: str = Depends(api_key_header)):
        if auth_api_key and api_key != auth_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
            )
        return api_key

    # MCPのエンドポイント定義
    @app.route("/mcp", methods=["GET", "POST"])
    async def mcp_endpoint(request: Request, _=Depends(api_key_auth)):
        # GETリクエスト：ツール一覧を返す
        if request.method == "GET":
            logger.info("Received GET request for tool list.")
            async def tool_list_generator():
                response = {"jsonrpc": "2.0", "id": "0", "result": {"tools": TOOL_DEFINITIONS}}
                yield f"data: {json.dumps(response)}\n\n"
            return StreamingResponse(tool_list_generator(), media_type="text/event-stream")

        # POSTリクエスト：ツールを実行する
        if request.method == "POST":
            body = await request.json()
            logger.info(f"Received POST request to execute tool: {json.dumps(body)}")
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
                logger.info(f"Tool '{tool_name}' executed successfully. Returning result.")
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
