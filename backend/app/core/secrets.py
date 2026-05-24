"""Optional secrets loader.

Supports fetching from AWS Secrets Manager when `SECRETS_PROVIDER=aws` and
`AWS_SECRETS_MANAGER_SECRET_NAME` is set. The secret should be a JSON object
whose keys map to environment variable names.

This module is intentionally defensive: if boto3 is not available or AWS
credentials are not configured, it logs a warning and returns without error.
"""
from __future__ import annotations

import os
import json
from typing import Dict


def load_remote_secrets() -> None:
    provider = os.environ.get('SECRETS_PROVIDER', '').lower()
    if provider != 'aws':
        return

    secret_name = os.environ.get('AWS_SECRETS_MANAGER_SECRET_NAME')
    if not secret_name:
        print('SECRETS_PROVIDER=aws but AWS_SECRETS_MANAGER_SECRET_NAME not set')
        return

    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except Exception:
        print('boto3 not available; skipping remote secrets load')
        return

    try:
        client = boto3.client('secretsmanager')
        resp = client.get_secret_value(SecretId=secret_name)
        secret_str = resp.get('SecretString')
        if not secret_str:
            print('Secret fetched but empty; skipping')
            return
        data: Dict[str, str] = json.loads(secret_str)
        for k, v in data.items():
            # only set if not already present; avoid overwriting env explicitly set
            if os.environ.get(k) is None:
                os.environ[k] = str(v)
        print(f'Loaded {len(data)} secrets from AWS Secrets Manager: {secret_name}')
    except (BotoCoreError, ClientError) as e:
        print(f'Failed to fetch secret {secret_name}: {e}')
    except json.JSONDecodeError:
        print('Secret value is not valid JSON; expected a JSON object mapping env var names to values')
