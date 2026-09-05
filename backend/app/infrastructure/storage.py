"""DocAssistIQ Backend — Object Storage infrastructure.

Provides a boto3 S3-compatible client factory and a probe function.
Uses MinIO in local development; swappable with AWS S3 in production.
"""

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings


def get_s3_client():
    """Return a configured boto3 S3 client for MinIO / S3."""
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.object_storage_endpoint,
        aws_access_key_id=settings.object_storage_access_key,
        aws_secret_access_key=settings.object_storage_secret_key,
        region_name=settings.object_storage_region,
        config=Config(
            connect_timeout=3,
            read_timeout=5,
            retries={"max_attempts": 0},  # no retries in probe
        ),
    )


def probe_storage() -> None:
    """Probe object storage connectivity. Raises on failure.

    Checks that the application bucket exists and is reachable.
    Called by the /ready endpoint.
    """
    settings = get_settings()
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=settings.object_storage_bucket)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "unknown")
        if error_code == "404":
            raise RuntimeError(
                f"Bucket '{settings.object_storage_bucket}' does not exist"
            ) from exc
        raise
    except BotoCoreError as exc:
        raise RuntimeError(f"Object storage unreachable: {exc}") from exc
