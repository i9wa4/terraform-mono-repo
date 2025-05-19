# app/slack_service.py
import logging

import requests

logger = logging.getLogger(__name__)


class SlackService:
    def post_to_response_url(self, response_url: str, message: str):
        try:
            payload = {
                "text": message,
                "response_type": (
                    "ephemeral"  # 'in_channel' または 'ephemeral' (一時的)
                ),
            }
            response = requests.post(response_url, json=payload, timeout=5)  #
            response.raise_for_status()
            logger.info(
                "Message posted to Slack via response_url. Status:"
                f" {response.status_code}"
            )
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error posting message to Slack response_url: {e}", exc_info=True
            )
            # ここでエラーを再スローすると、エラー報告がループする可能性があるため注意
