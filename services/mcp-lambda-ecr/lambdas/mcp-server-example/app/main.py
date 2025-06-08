import json
import logging
import os

import boto3
from app.mcp_server import mcp
from botocore.exceptions import BotoCoreError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_secret_value(
    secret_name: str, secret_key: str, region_name: str = os.environ.get("AWS_REGION")
) -> str:
    """AWS Secrets Managerからシークレット値を取得"""
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret_payload = response["SecretString"]
        secret_data = json.loads(secret_payload)
        if secret_key not in secret_data:
            # このKeyErrorは呼び出し元でキャッチされるか、Lambda実行を失敗させる
            raise KeyError(f"Key '{secret_key}' not found in secret '{secret_name}'.")
        value = secret_data[secret_key]
        logger.info(
            f"Successfully retrieved secret '{secret_name}' (key: '{secret_key}')"
        )
        return value
    except (BotoCoreError, json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error(
            f"Error processing secret '{secret_name}' (key: '{secret_key}'):"
            f" {type(e).__name__} - {str(e)}"
        )
        raise  # エラーを再raiseし、呼び出し元で処理されるかLambda実行を失敗させる


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

    # --- APIキー取得 ---
    expected_api_key = None
    try:
        expected_api_key = get_secret_value(
            os.environ.get("COMMON_SECRET_NAME"), "X_API_KEY"
        )

    except KeyError as e:
        # 環境変数が設定されていない場合
        logger.error(
            "CRITICAL: Environment variable for API key secret name not set"
            f" ('{str(e)}'). Denying request."
        )
        req_id_for_error_response = None
        body_for_id_parsing_error = event.get("body", "{}")
        if isinstance(body_for_id_parsing_error, str):
            body_for_id_parsing_error = json.loads(body_for_id_parsing_error)
        req_id_for_error_response = body_for_id_parsing_error.get("id")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32001,
                        "message": (
                            "Server configuration error: API Key secret name not"
                            f" configured ({str(e)})"
                        ),
                    },
                    "id": req_id_for_error_response,
                }
            ),
        }
    except Exception as e:
        # get_secret_value内でキャッチされなかった予期せぬエラー (例: IAM権限不足、シークレット存在しない等)
        logger.error(
            f"CRITICAL: Failed to load expected API key due to: {type(e).__name__} -"
            f" {str(e)}. Denying request."
        )
        req_id_for_error_response = None
        body_for_id_parsing_error = event.get("body", "{}")
        if isinstance(body_for_id_parsing_error, str):
            body_for_id_parsing_error = json.loads(body_for_id_parsing_error)
        req_id_for_error_response = body_for_id_parsing_error.get("id")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32001,
                        "message": (
                            "Server configuration error: Could not retrieve API Key"
                            f" ({type(e).__name__})"
                        ),
                    },
                    "id": req_id_for_error_response,
                }
            ),
        }

    # --- APIキー検証 ---
    request_headers = event.get("headers", {})
    received_api_key = None
    # クライアントが送信するヘッダー名を小文字で定義 (例: "x-api-key")
    client_api_key_header_name_to_check_lower = "x-api-key"

    for header_key, header_value in request_headers.items():
        if header_key.lower() == client_api_key_header_name_to_check_lower:
            received_api_key = header_value
            break

    if not received_api_key or received_api_key != expected_api_key:
        logger.warning(
            f"Forbidden: Missing or invalid API key. Received key: '{received_api_key}'"
        )
        req_id_for_error_response = None
        body_for_id_parsing_error = event.get("body", "{}")
        if isinstance(body_for_id_parsing_error, str):
            body_for_id_parsing_error = json.loads(body_for_id_parsing_error)
        req_id_for_error_response = body_for_id_parsing_error.get("id")
        return {
            "statusCode": 403,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "Forbidden - Invalid API Key"},
                    "id": req_id_for_error_response,
                }
            ),
        }
    logger.info("API key validated successfully.")
    # --- APIキー取得と検証ここまで ---

    # --- リクエストボディの処理 (ここから下は変更なし) ---
    try:
        if isinstance(event.get("body"), str):
            request_body_str = event["body"]
        elif isinstance(event.get("body"), dict):
            request_body_str = json.dumps(event["body"])
        else:
            request_body_str = json.dumps(event)

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
    except TypeError as e:
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
    except Exception as e:
        logger.error(
            f"メソッド '{method}' の実行中にエラーが発生しました: {e}", exc_info=True
        )
        response_data = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32000,
                "message": f"メソッド実行中のサーバーエラー: {str(e)}",
            },
            "id": request_id,
        }
        lambda_status_code = 500

    response_body_str = json.dumps(response_data, ensure_ascii=False)
    logger.info(
        f"レスポンス送信 (ステータス {lambda_status_code}): {response_body_str}"
    )

    return {
        "statusCode": lambda_status_code,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": response_body_str,
    }
