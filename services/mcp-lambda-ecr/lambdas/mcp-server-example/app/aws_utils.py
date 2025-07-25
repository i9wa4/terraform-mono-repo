import json
import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
            取得したシークレットの値。シークレットの取得に失敗した場合はNoneを返す。
    """
    if not secret_name:
        logger.error("Secret name is not provided.")
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
        if secret_key:
            secret_dict = json.loads(secret)
            return secret_dict.get(secret_key)
        else:
            return secret  # JSON文字列全体を返す
    except (ClientError, KeyError, json.JSONDecodeError) as e:
        if secret_key:
            logger.warning(f"Key '{secret_key}' not found in secret '{secret_name}'.")
        else:
            logger.warning(
                f"Could not retrieve or parse the secret '{secret_name}'. Error: {e}"
            )
        return None
