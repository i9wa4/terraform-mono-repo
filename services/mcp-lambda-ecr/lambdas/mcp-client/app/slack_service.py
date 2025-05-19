# app/slack_service.py
import logging

import requests

logger = logging.getLogger(__name__)


class SlackService:
    def __init__(self, webhook_url: str = None):  # Webhook URLをオプショナルに
        self.webhook_url = webhook_url

    def post_to_webhook(self, message: str):
        if not self.webhook_url:
            logger.error("Slack Webhook URL is not configured for post_to_webhook.")
            raise ValueError("Slack Webhook URL is required for posting to webhook.")
        try:
            payload = {"text": message}
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            response.raise_for_status()
            logger.info(
                f"Message posted to Slack webhook. Status: {response.status_code}"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Error posting message to Slack webhook: {e}", exc_info=True)

    def post_to_response_url(self, response_url: str, message: str):
        if not response_url:
            logger.error("Slack response_url is not provided.")
            raise ValueError("Slack response_url is required for this operation.")
        try:
            payload = {"text": message, "response_type": "ephemeral"}
            response = requests.post(response_url, json=payload, timeout=5)
            response.raise_for_status()
            logger.info(
                "Message posted to Slack via response_url. Status:"
                f" {response.status_code}"
            )
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error posting message to Slack response_url: {e}", exc_info=True
            )
