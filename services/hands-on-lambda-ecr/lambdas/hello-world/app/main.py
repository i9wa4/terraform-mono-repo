import json
import logging
import sys

import boto3

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
    logger.info("Checking non-standard library: boto3")
    try:
        s3 = boto3.client("s3")
        s3_buckets_response = s3.list_buckets()
        logger.info(f"Available S3 buckets: {s3_buckets_response['Buckets']}")
    except Exception as e:
        logger.error(f"Error interacting with S3: {e}")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "message": (
                    f"Hello from AWS Lambda using Python {sys.version} in a container!"
                ),
                "event_received": event,
            }
        ),
    }
