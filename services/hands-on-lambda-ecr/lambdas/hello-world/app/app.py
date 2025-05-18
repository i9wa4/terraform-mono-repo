import json
import sys


def handler(event, context):
    """
    Lambda 関数のメインハンドラ。
    イベントを受け取り、挨拶メッセージを返します。
    """
    print("Lambda function invoked!")
    print(f"Received event: {json.dumps(event)}")

    python_version = sys.version
    message = f"Hello from AWS Lambda using Python {python_version} in a container!"

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": message, "event_received": event}),
    }
