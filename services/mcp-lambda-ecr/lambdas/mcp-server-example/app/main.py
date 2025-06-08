import os
import logging
from mangum import Mangum
from app.aws_utils import get_secret_value
from app.server import create_app

# --- Logging Configuration ---
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --- Environment Variables ---
# Lambdaの環境変数として設定する
COMMON_SECRET_NAME = os.environ.get("COMMON_SECRET_NAME")

# --- Initialization at Cold Start ---
app = None
try:
    logger.info("Initializing application at cold start...")

    # 1. 外部ツール(Google)用のAPIキーを環境変数に設定
    google_api_key = get_secret_value(COMMON_SECRET_NAME, "GOOGLE_API_KEY")
    google_cse_id = get_secret_value(COMMON_SECRET_NAME, "GOOGLE_CSE_ID")
    if google_api_key:
        os.environ["GOOGLE_API_KEY"] = google_api_key
    if google_cse_id:
        os.environ["GOOGLE_CSE_ID"] = google_cse_id

    # 2. このサーバー自身を保護するためのAPIキーを取得
    x_api_key = get_secret_value(COMMON_SECRET_NAME, "X_API_KEY")

    # 3. サーバー本体のファクトリ関数を呼び出し、FastAPIアプリを生成
    #    このappインスタンスにサーバーの全ロジックが詰まっている
    app = create_app(auth_api_key=x_api_key)

    logger.info("Application initialized successfully.")

except Exception as e:
    logger.critical(f"Failed to initialize the application: {e}", exc_info=True)
    # 初期化失敗時にエラーを返すダミーアプリを作成
    from fastapi import FastAPI
    app = FastAPI()
    @app.get("/{path:path}")
    def critical_error_handler(path: str):
        raise RuntimeError("Application failed to initialize. Check logs.") from e

# --- Lambda Handler ---
# MangumがLambdaイベントをFastAPIアプリに中継する
# 変数名を 'handler' から 'lambda_handler' に変更
lambda_handler = Mangum(app, lifespan="off")
