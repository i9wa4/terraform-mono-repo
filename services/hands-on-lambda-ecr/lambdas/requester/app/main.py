import json
import logging
import sys

import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """AWS Lambda function handler.
    Try to make an HTTP GET request to a target URL and return the response.

    Parameters:
        event (dict): The event data passed to the Lambda function.
        context (LambdaContext): The context object providing runtime information.

    Returns:
        dict: A response object containing the status code, headers, and body.
    """
    logger.info("Lambda function invoked!")
    logger.info(f"Received event: {json.dumps(event)}")
    logger.info(f"Context (request_id): {getattr(context, 'aws_request_id', 'N/A')}")

    target_url = "https://www.google.com"
    request_timeout = 5

    try:
        response = requests.get(target_url, timeout=request_timeout)
        response_text_preview = (
            (response.text[:100] + "..." if len(response.text) > 100 else response.text)
            if response.text
            else ""
        )

        if 200 <= response.status_code < 300:
            logger.info(
                f"Request to {target_url} successful. Status: {response.status_code}."
                f" Preview: {response_text_preview}"
            )
            message = (
                f"Successfully called {target_url}. External API status:"
                f" {response.status_code}. Python {sys.version}."
            )
            lambda_status_code_to_return = 200
        else:
            logger.warning(
                f"Request to {target_url} returned an error status:"
                f" {response.status_code}. Preview: {response_text_preview}"
            )
            message = (
                f"Call to {target_url} returned status {response.status_code}. Python"
                f" {sys.version}."
            )
            lambda_status_code_to_return = response.status_code

        return_body = {
            "message": message,
            "external_api_status": response.status_code,
            "external_response_preview": response_text_preview,
            "event_received": event,
        }
        return {
            "statusCode": lambda_status_code_to_return,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(return_body),
        }

    except requests.exceptions.RequestException as e:
        logger.error(
            f"Failed to request {target_url} due to a requests library exception: {e}"
        )
        return {
            "statusCode": 502,  # Bad Gateway
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "error": f"Failed to connect to or communicate with {target_url}.",
                    "details": str(e),
                }
            ),
        }

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return {
            "statusCode": 500,  # Internal Server Error
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "error": (
                        "An unexpected internal error occurred in the Lambda function."
                    ),
                    "details": str(e),
                }
            ),
        }
