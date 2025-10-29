"""S3 utilities for uploading files and generating presigned URLs."""

from typing import Optional
import boto3


def get_s3_client():
    """Return a boto3 S3 client using default AWS credentials in Lambda."""
    return boto3.client("s3")


def upload_bytes_to_s3(
    bucket: str,
    key: str,
    data: bytes,
    content_type: Optional[str] = None,
) -> None:
    """Upload raw bytes to S3 as an object.

    Args:
        bucket: Target S3 bucket name.
        key: Object key/path inside the bucket.
        data: Raw bytes to upload.
        content_type: Optional MIME type for the object.
    """
    s3 = get_s3_client()
    put_kwargs = {
        "Bucket": bucket,
        "Key": key,
        "Body": data,
    }
    if content_type:
        put_kwargs["ContentType"] = content_type
    s3.put_object(**put_kwargs)


def generate_presigned_get_url(
    bucket: str,
    key: str,
    expires_in_seconds: int,
) -> str:
    """Generate a presigned GET URL for an S3 object.

    Args:
        bucket: S3 bucket name.
        key: Object key within the bucket.
        expires_in_seconds: URL expiration in seconds.

    Returns:
        A presigned URL for HTTP GET.
    """
    s3 = get_s3_client()
    return s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in_seconds,
    )


def get_object_bytes(bucket: str, key: str) -> bytes:
    """Download an object's bytes from S3.

    Args:
        bucket: S3 bucket name
        key: Object key within the bucket

    Returns:
        Raw bytes of the object
    """
    s3 = get_s3_client()
    resp = s3.get_object(Bucket=bucket, Key=key)
    return resp["Body"].read()


