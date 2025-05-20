# services/mcp-lambda-ecr/lambdas/mcp-client/app/config.py
import json
import logging
import os

import boto3

logger = logging.getLogger(__name__)


class AppConfig:
    def __init__(self):
        self._gemini_api_key = self._load_secret_value(
            os.environ.get("MCP_CLIENT_SECRET_NAME"), "GEMINI_API_KEY"
        )
        self._mcp_server_url = self._load_secret_value(
            os.environ.get("MCP_SERVER_EXAMPLE_SECRET_NAME"), "FUNCTION_URL"
        )
        logger.info("AppConfig initialized: MCP_SERVER_URL and GEMINI_API_KEY loaded.")

    def _load_secret_value(self, secret_name_env_var: str, secret_key: str) -> str:
        if not secret_name_env_var:
            raise ValueError(
                f"Environment variable for secret name '{secret_name_env_var}' (for key"
                f" '{secret_key}') is not set."
            )

        secret_name = secret_name_env_var  # Actual secret name from env var
        if not secret_name:  # Re-check if the env var itself was empty
            raise ValueError(
                f"Secret name resolved from env var for key '{secret_key}' is empty."
            )

        logger.info(f"Attempting to load secret '{secret_name}' for key '{secret_key}'")
        try:
            session = boto3.session.Session()
            client = session.client(service_name="secretsmanager")
            get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        except Exception as e:
            logger.error(
                f"Failed to retrieve secret '{secret_name}' from Secrets Manager: {e}",
                exc_info=True,
            )
            raise ValueError(f"Failed to retrieve secret '{secret_name}': {e}") from e

        if "SecretString" in get_secret_value_response:
            secret_string = get_secret_value_response["SecretString"]
            try:
                secret_dict = json.loads(secret_string)
                value = secret_dict.get(secret_key)
                if not value:
                    raise ValueError(
                        f"Key '{secret_key}' not found in secret '{secret_name}'."
                    )
                return value
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse SecretString for '{secret_name}' as JSON: {e}",
                    exc_info=True,
                )
                raise ValueError(
                    f"SecretString for '{secret_name}' is not valid JSON."
                ) from e
        else:
            # Binary secret not supported in this context
            raise ValueError(
                f"SecretString not found for secret '{secret_name}'. Binary secrets are"
                " not supported here."
            )

    @property
    def gemini_api_key(self) -> str:
        if not self._gemini_api_key:  # Should be caught by constructor
            raise ValueError("Gemini API Key is not loaded.")
        return self._gemini_api_key

    @property
    def mcp_server_url(self) -> str:
        if not self._mcp_server_url:  # Should be caught by constructor
            raise ValueError("MCP Server URL is not loaded.")
        return self._mcp_server_url
