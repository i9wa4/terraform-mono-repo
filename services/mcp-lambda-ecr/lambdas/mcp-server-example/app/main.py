import json
import logging

from app.mcp_server import mcp

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    MCPサーバーのサンプル用 AWS Lambda 関数ハンドラ。
    イベントボディに JSON-RPC ライクなリクエストを想定します。
    """
    logger.info(
        "Lambda関数が呼び出されました。リクエストID:"
        f" {getattr(context, 'aws_request_id', 'N/A')}"
    )
    logger.debug(f"受信イベント: {json.dumps(event)}")

    try:
        # API Gateway や他のトリガーはボディを文字列として渡す場合があります。
        # Content-Type ヘッダーが application/json の場合、API Gateway が
        # 自動的に辞書にパースすることがあります。
        if isinstance(event.get("body"), str):
            request_body_str = event["body"]
        elif isinstance(
            event.get("body"), dict
        ):  # API Gateway によって既にパースされている場合
            request_body_str = json.dumps(event["body"])
        else:  # 他のイベント構造やLambdaの直接呼び出しの場合のフォールバック
            request_body_str = json.dumps(event)  # イベント全体をリクエストとして扱う

        logger.info(f"MCPリクエストのパース試行: {request_body_str}")
        request_obj = json.loads(request_body_str)

    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError: リクエストのパースに失敗しました: {e}")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": f"パースエラー: {e}"},
                    "id": None,
                }
            ),
        }
    except TypeError as e:  # event["body"] が None や文字列/辞書でない場合を処理
        logger.error(
            f"TypeError: 無効なリクエスト入力: {e}. イベントボディ: {event.get('body')}"
        )
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32600, "message": f"無効なリクエスト: {e}"},
                    "id": None,
                }
            ),
        }

    method = request_obj.get("method")
    params = request_obj.get("params", {})
    request_id = request_obj.get("id")

    if not method:
        logger.error("リクエストにメソッドが指定されていません。")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32600,
                        "message": "無効なリクエスト: 'method' がありません。",
                    },
                    "id": request_id,
                }
            ),
        }

    response_data = None
    lambda_status_code = 200

    try:
        logger.info(
            f"MCPメソッド '{method}' をパラメータ {json.dumps(params)} で処理中"
        )
        # FastMCP インスタンスに登録されたツールとリソースへのアクセス
        # 正確な構造 (mcp.router.tools, mcp.router.resources) は FastMCP の設計に依存します。
        # これらは一般的な規約です。
        if (
            hasattr(mcp, "router")
            and hasattr(mcp.router, "tools")
            and method in mcp.router.tools
        ):
            tool_definition = mcp.router.tools[method]
            actual_tool_func = tool_definition.func
            logger.info(f"ツール '{method}' を呼び出し中。")
            result = actual_tool_func(**params)
            response_data = {"jsonrpc": "2.0", "result": result, "id": request_id}
        elif (
            hasattr(mcp, "router")
            and hasattr(mcp.router, "resources")
            and method in mcp.router.resources
        ):
            resource_definition = mcp.router.resources[method]
            actual_resource_func = resource_definition.func
            logger.info(f"リソース '{method}' を呼び出し中。")
            # リソースはツールと同じようにパラメータを期待するとは限りません。
            # FastMCP がリソースのパラメータを異なる方法で処理する場合は調整してください。
            result = actual_resource_func(**params)
            response_data = {"jsonrpc": "2.0", "result": result, "id": request_id}
        else:
            logger.warning(
                f"メソッド '{method}' はMCPツールまたはリソースに見つかりませんでした。"
            )
            response_data = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"メソッドが見つかりません: {method}",
                },
                "id": request_id,
            }
            # "メソッドが見つかりません" の場合、JSON-RPC 仕様では通常 HTTP 200 を返しますが、
            # JSON ボディにエラーを含めます。一部のゲートウェイは 404 を好むかもしれません。
            # この特定のエラーについては、一部の JSON-RPC サーバー実装に従い 200 を維持します。
            # lambda_status_code = 404 # または 200 を維持
    except Exception as e:
        logger.error(
            f"メソッド '{method}' の実行中にエラーが発生しました: {e}", exc_info=True
        )
        response_data = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32000,
                "message": f"メソッド実行中のサーバーエラー: {e}",
            },
            "id": request_id,
        }
        lambda_status_code = 500  # 内部サーバーエラー

    response_body_str = json.dumps(response_data, ensure_ascii=False)
    logger.info(
        f"レスポンス送信 (ステータス {lambda_status_code}): {response_body_str}"
    )

    return {
        "statusCode": lambda_status_code,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": response_body_str,
    }
