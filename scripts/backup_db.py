#!/usr/bin/env python3
"""Dump Postgres database and upload to S3 bucket.

Environment variables:
- DATABASE_URL or DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME
- AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
- S3_BUCKET
- S3_PREFIX (optional)
"""
import os
import subprocess
import tempfile
import datetime
import sys

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except Exception:
    boto3 = None


def get_db_params():
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        return {'database_url': database_url}
    # fallback to individual vars
    return {
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD', ''),
        'host': os.environ.get('DB_HOST', 'postgres'),
        'port': os.environ.get('DB_PORT', '5432'),
        'name': os.environ.get('DB_NAME', 'eldercare'),
    }


def run_pg_dump(out_path: str) -> None:
    params = get_db_params()
    if 'database_url' in params:
        cmd = ['pg_dump', params['database_url'], '-Fc', '-f', out_path]
    else:
        cmd = [
            'pg_dump',
            '-h', params['host'],
            '-p', params['port'],
            '-U', params['user'],
            '-Fc',
            '-f', out_path,
            params['name'],
        ]
    env = os.environ.copy()
    if 'password' in params and params.get('password'):
        env['PGPASSWORD'] = params['password']
    subprocess.check_call(cmd, env=env)


def upload_to_s3(file_path: str, bucket: str, key: str) -> None:
    if boto3 is None:
        raise RuntimeError('boto3 not installed')
    s3 = boto3.client('s3')
    try:
        s3.upload_file(file_path, bucket, key)
    except (BotoCoreError, ClientError) as e:
        raise


def main():
    bucket = os.environ.get('S3_BUCKET')
    if not bucket:
        print('S3_BUCKET not set; aborting backup', file=sys.stderr)
        sys.exit(2)
    prefix = os.environ.get('S3_PREFIX', 'backups')

    ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    filename = f'pgdump-{ts}.dump'
    key = f"{prefix}/{filename}"

    with tempfile.TemporaryDirectory() as td:
        out_path = os.path.join(td, filename)
        print('Running pg_dump...', file=sys.stderr)
        run_pg_dump(out_path)
        print('Uploading to S3...', file=sys.stderr)
        upload_to_s3(out_path, bucket, key)
        print(f'Uploaded to s3://{bucket}/{key}', file=sys.stderr)


if __name__ == '__main__':
    main()
