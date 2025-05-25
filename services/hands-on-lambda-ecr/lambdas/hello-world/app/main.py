import json
import logging
import sys

import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda 関数のメインハンドラ。
    イベントを受け取り、挨拶メッセージを返します。
    """
    logger.info("Lambda function invoked!")
    logger.info(f"Received event: {json.dumps(event)=}")
    logger.info(f"Received context: {context=}")

    # 標準ライブラリ以外の動作確認
    try:
        response = requests.get("https://www.google.com")
        logger.info(f"Response status code: {response.status_code}")

        if response.status_code == 200:
            logging.info(f"Request successful. Response: {response.text[:100]}...")
        else:
            logging.error(f"Request failed. Response: {response.text[:100]}...")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "message": (
                        f"Hello from AWS Lambda using Python {sys.version} in a"
                        " container!"
                    ),
                    "event_received": event,
                }
            ),
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while making a request: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)}),
        }
