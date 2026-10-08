from io import BytesIO

from app.services.storage import upload_file, s3, S3_BUCKET


def test_upload_file_to_moto():
    file_key = "tests/test-upload.jpg"
    content = b"fake scan image"

    upload_file(
        file_object=BytesIO(content),
        file_key=file_key,
        content_type="image/jpeg",
    )

    response = s3.get_object(
        Bucket=S3_BUCKET,
        Key=file_key,
    )

    assert response["ContentType"] == "image/jpeg"
    assert response["Body"].read() == content