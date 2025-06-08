import json
import logging
import os

from app.aws_utils import get_secret_value
from app.server import create_app
from mangum import Mangum

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Environment Variables ---
# このラッパー自身のAPIキーが入ったSecret名
AUTH_SECRET_NAME = os.environ.get("COMMON_SECRET_NAME")
# ラップ対象のサーバーが必要とする設定(環境変数)がJSON形式で入ったSecret名
CONFIG_SECRET_NAME = os.environ.get("CONFIG_SECRET_NAME")

# --- Initialization at Cold Start ---
app = None
try:
    logger.info("Initializing application at cold start...")

    # 1. ラッパー自身の認証用APIキーを取得
    auth_api_key = get_secret_value(AUTH_SECRET_NAME, "X_API_KEY")
    if not auth_api_key:
        raise ValueError("Auth API key (X_API_KEY) could not be retrieved.")

    # 2. ラップ対象サーバー用の設定を読み込み、環境変数として設定
    config_json_str = get_secret_value(
        CONFIG_SECRET_NAME, secret_key=None
    )  # secret_key=NoneでSecret全体を取得
    if config_json_str:
        try:
            env_vars_to_set = json.loads(config_json_str)
            for key, value in env_vars_to_set.items():
                os.environ[key] = str(value)
            logger.info(
                f"Successfully set {len(env_vars_to_set)} environment variables for"
                " target server."
            )
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse secret '{CONFIG_SECRET_NAME}' as JSON.")

    # 3. FastAPIアプリケーションを生成
    app = create_app(auth_api_key=auth_api_key)

    logger.info("Application initialized successfully.")

except Exception as e:
    initialization_error = e  # 例外を別の変数に保存
    logger.critical(
        f"Failed to initialize the application: {initialization_error}", exc_info=True
    )
    from fastapi import FastAPI
    from fastapi import status

    # エラー報告専用のFastAPIアプリを作成
    error_app = FastAPI()

    @error_app.get("/{path:path}", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    def critical_error_handler(path: str):
        # 保存した変数を参照する
        return {
            "detail": (
                "Service unavailable due to initialization failure:"
                f" {initialization_error}"
            )
        }

    app = error_app  # グローバルのapp変数にエラー報告用アプリをセット

# --- Lambda Handler ---
lambda_handler = Mangum(app, lifespan="off")
