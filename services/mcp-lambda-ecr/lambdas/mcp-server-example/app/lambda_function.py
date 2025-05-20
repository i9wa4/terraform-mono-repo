# services/mcp-lambda-ecr/lambdas/mcp-server-example/app/lambda_function.py
from app.request_handler import handle_request  # app.request_handler を想定
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer

logger = Logger()
tracer = Tracer()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    # handle_request がLambdaプロキシ統合レスポンス形式の辞書を返す
    return handle_request(event, context, logger)
