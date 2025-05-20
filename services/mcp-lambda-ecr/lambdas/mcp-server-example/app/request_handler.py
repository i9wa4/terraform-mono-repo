# services/mcp-lambda-ecr/lambdas/mcp-server-example/app/request_handler.py
import json
import random
import time

# from aws_lambda_powertools import Logger # Not needed if logger is passed as argument


def handle_request(event, context, logger):  # Accept context and logger
    """
    Handles the incoming request, processes it, and returns a response payload.
    The statusCode for the HTTP response should be determined in lambda_handler
    or returned by this function within the response_data dict.
    """
    request_id = context.aws_request_id if context else "N/A"
    logger.info(f"Request ID: {request_id} - Handling request within request_handler.")

    try:
        raw_body = event.get("body")
        parsed_body = None

        if isinstance(raw_body, str):
            try:
                parsed_body = json.loads(raw_body)
                logger.info(
                    f"Request ID: {request_id} - Successfully parsed JSON body."
                )
            except json.JSONDecodeError as e:
                logger.error(
                    f"Request ID: {request_id} - Failed to parse JSON body: {str(e)}"
                )
                return {
                    "statusCode": 400,  # Bad Request
                    "error": "Invalid JSON in request body",
                    "details": str(e),
                }
        elif isinstance(raw_body, dict):
            # Body is already a dictionary (e.g., from a direct Lambda invoke for testing)
            parsed_body = raw_body
            logger.info(f"Request ID: {request_id} - Body is already a dictionary.")
        else:
            logger.warn(
                f"Request ID: {request_id} - Event body is not a string or dict, or is"
                " missing."
            )
            # Depending on requirements, could be an error or proceed with defaults
            parsed_body = {}

        user_query = parsed_body.get("query", "No query provided")
        logger.info(f"Request ID: {request_id} - User query: '{user_query}'")

        # Simulate some processing time (e.g., calling an AI model, DB query)
        time.sleep(random.uniform(0.1, 0.3))  # Reduced for quicker testing

        response_message = (
            f"MCP Server Example received your query: '{user_query}'. This is a dummy"
            " response from the server."
        )

        # Prepare the data to be returned.
        # This will be the content of the 'body' in the final HTTP response (after json.dumps).
        return {
            "statusCode": 200,  # Explicitly set success status code
            "message": response_message,
            "query_received": user_query,
            "request_id": request_id,
        }

    except Exception as e:
        # Log the exception here for detailed context from request_handler
        logger.exception(
            f"Request ID: {request_id} - An error occurred in handle_request."
        )
        # Return an error structure that lambda_handler can use,
        # or re-raise to let lambda_handler create a generic 500 error.
        # For more control, return a dict with statusCode.
        return {
            "statusCode": 500,  # Internal Server Error
            "error": "An error occurred while processing your request in the handler.",
            "details": str(e),
            "request_id": request_id,
        }
