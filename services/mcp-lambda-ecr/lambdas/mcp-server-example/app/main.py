import os
import logging
from mangum import Mangum
from app.aws_utils import get_secret_value
from app.server import create_app

# --- Logging Configuration ---
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --- Environment Variables ---
COMMON_SECRET_NAME = os.environ.get("COMMON_SECRET_NAME")

# --- Initialization at Cold Start ---
app = None
try:
    logger.info("Initializing application at cold start...")

    # Google関連のシークレット読み込み処理を削除
    # # 1. 外部ツール(Google)用のAPIキーを環境変数に設定
    # google_api_key = get_secret_value(COMMON_SECRET_NAME, "GOOGLE_API_KEY")
    # google_cse_id = get_secret_value(COMMON_SECRET_NAME, "GOOGLE_CSE_ID")
    # ...

    # このサーバー自身を保護するためのAPIキーのみ取得
    x_api_key = get_secret_value(COMMON_SECRET_NAME, "X_API_KEY")

    # サーバー本体のファクトリ関数を呼び出し、FastAPIアプリを生成
    app = create_app(auth_api_key=x_api_key)

    logger.info("Application initialized successfully.")

except Exception as e:
    logger.critical(f"Failed to initialize the application: {e}", exc_info=True)
    from fastapi import FastAPI, status

    app = FastAPI()
    @app.get("/{path:path}", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    def critical_error_handler(path: str):
        return {"detail": f"Service unavailable due to initialization failure: {e}"}


# --- Lambda Handler ---
lambda_handler = Mangum(app, lifespan="off")
