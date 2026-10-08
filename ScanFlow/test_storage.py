from io import BytesIO

from app.services.storage import upload_file, s3


upload_file(
    BytesIO(b"ScanFlow storage test"),
    "scans/test-storage.txt",
    "text/plain",
)

response = s3.get_object(
    Bucket="scanflow-scans",
    Key="scans/test-storage.txt",
)

content = response["Body"].read().decode()

print(content)