import json
import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_secret_value(secret_name: str, secret_key: str) -> str | None:
    """AWS Secrets Managerから指定されたキーの値を取得する。

    指定されたシークレット名（secret_name）でSecrets Managerからシークレットを取得し、
    その内容をJSONとして解析する。解析後、指定されたキー（secret_key）に対応する値を返す。
    シークレットがJSON形式でない場合は、シークレットの文字列全体をそのまま返す。

    Args:
        secret_name (str): 取得対象のシークレットの名前。
        secret_key (str): シークレット内で値を取得したいキーの名前。

    Returns:
        str | None:
            取得したシークレットの値。シークレットの取得に失敗した場合や、
            JSON形式のシークレット内にキーが存在しない場合はNoneを返す。
    """
    if not secret_name or not secret_key:
        logger.error("Secret name or secret key is not provided.")
        return None

    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager")

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logger.error(f"Failed to retrieve secret '{secret_name}': {e}")
        return None

    secret = get_secret_value_response.get("SecretString")
    if not secret:
        logger.error(f"SecretString is empty for secret '{secret_name}'.")
        return None

    try:
        secret_dict = json.loads(secret)
        value = secret_dict.get(secret_key)
        if value is None:
            logger.warning(f"Key '{secret_key}' not found in secret '{secret_name}'.")
        return value
    except json.JSONDecodeError:
        # シークレットがJSON形式でない場合、そのまま返す
        logger.info(
            f"Secret '{secret_name}' is not a JSON object. Returning as plain text."
        )
        return secret
