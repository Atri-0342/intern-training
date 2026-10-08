import boto3
from io import BytesIO

s3 = boto3.client(
    "s3",
    region_name="us-east-1",
    endpoint_url="http://localhost:5000",
    aws_access_key_id="test",
    aws_secret_access_key="test",
)

s3.upload_fileobj(
    BytesIO(b"ScanFlow test file"),
    "scanflow-scans",
    "test.txt",
)

print("Upload successful")