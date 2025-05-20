# services/mcp-lambda-ecr/lambdas/mcp-server-example/app/lambda_function.py
import json

# AWS Lambda Powertools for Python
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer
from request_handler import handle_request

# from aws_lambda_powertools.utilities.typing import LambdaContext # Future: if using context type hints

# Initialize Powertools
# POWERTOOLS_SERVICE_NAME is typically set in Lambda environment variables
logger = Logger()
tracer = Tracer()

# Import the request handler (using relative import for clarity within the 'app' package)


@tracer.capture_lambda_handler
@logger.inject_lambda_context(
    log_event=True
)  # Automatically logs the event if POWERTOOLS_LOGGER_LOG_EVENT is true
def lambda_handler(event, context):  # context type can be LambdaContext
    # logger.info(f"Received event: {json.dumps(event)}") # Logged by inject_lambda_context if log_event=True
    # logger.info(f"Context: {context}") # For debugging context object if needed

    try:
        # Pass the event, context, and logger to the handler for business logic
        response_data = handle_request(event, context, logger)

        logger.info("Successfully processed event.")
        return {
            "statusCode": response_data.get(
                "statusCode", 200
            ),  # Allow handler to set statusCode
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response_data),
        }
    except Exception as e:
        # Log the exception with stack trace
        logger.exception("Error processing request in lambda_handler.")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "error": "Internal server error",
                    "request_id": context.aws_request_id if context else None,
                    "details": str(e),  # Include exception details for debugging
                }
            ),
        }
