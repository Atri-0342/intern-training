import os
from typing import BinaryIO

import boto3


S3_BUCKET = os.getenv(
    "S3_BUCKET",
    "scanflow-scans",
)

S3_REGION = os.getenv(
    "S3_REGION",
    "us-east-1",
)

S3_ENDPOINT_URL = os.getenv(
    "S3_ENDPOINT_URL",
    "http://host.docker.internal:5000",
)

s3 = boto3.client(
    "s3",
    region_name=S3_REGION,
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=os.getenv(
        "AWS_ACCESS_KEY_ID",
        "test",
    ),
    aws_secret_access_key=os.getenv(
        "AWS_SECRET_ACCESS_KEY",
        "test",
    ),
)


def upload_file(
    file_object: BinaryIO,
    file_key: str,
    content_type: str,
) -> None:
    s3.upload_fileobj(
        file_object,
        S3_BUCKET,
        file_key,
        ExtraArgs={
            "ContentType": content_type,
        },
    )


def delete_file(
    file_key: str,
) -> None:
    s3.delete_object(
        Bucket=S3_BUCKET,
        Key=file_key,
    )