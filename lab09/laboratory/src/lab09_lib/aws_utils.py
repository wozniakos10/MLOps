import os

import boto3

from lab09_lib.logger import get_configured_logger

logger = get_configured_logger()


def upload_file_to_s3(file_name, bucket, object_name=None):
    """function for uploading file to s3

    Args:
        file_name (_type_): _description_
        bucket (_type_): _description_
        object_name (_type_, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client("s3")
    try:
        s3_client.upload_file(file_name, bucket, object_name)
    except Exception as e:
        logger.info(f"Error uploading file to S3: {e}")
        return False
    return True


def download_file_from_s3(bucket, object_name, file_name=None):
    """function for downloading file from s3

    Args:
        bucket (_type_): _description_
        object_name (_type_): _description_
        file_name (_type_, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """

    # If S3 object_name was not specified, use file_name
    if file_name is None:
        file_name = object_name
    if os.path.exists(file_name):
        logger.info(f"File {file_name} already exists. Skipping download.")
        return True

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    # Download the file
    s3_client = boto3.client("s3")
    try:
        s3_client.download_file(bucket, object_name, file_name)
    except Exception as e:
        logger.info(f"Error downloading file from S3: {e}")
        return False
    return True


def download_folder_from_s3(bucket, prefix, local_dir):
    """function for downloading folder from s3

    Args:
        bucket (_type_): _description_
        prefix (_type_): _description_
        local_dir (_type_): _description_
    """

    s3_resource = boto3.resource("s3")
    bucket_obj = s3_resource.Bucket(bucket)

    for obj in bucket_obj.objects.filter(Prefix=prefix):
        # Skip if it's a directory marker (ends with /)
        if obj.key.endswith("/"):
            continue

        # Calculate the relative path from the prefix
        relative_path = os.path.relpath(obj.key, prefix)
        target_path = os.path.join(local_dir, relative_path)

        # Create directories if they don't exist
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        # Download the file
        try:
            bucket_obj.download_file(obj.key, target_path)
            logger.info(f"Downloaded {obj.key} to {target_path}")
        except Exception as e:
            logger.info(f"Error downloading {obj.key}: {e}")


if __name__ == "__main__":
    download_file_from_s3(
        bucket="test-bucket-mlops-lab9",
        object_name="models/models_lab_9/classifier.joblib",
        file_name="large_models/model/classifier.joblib",
    )

    download_folder_from_s3(
        bucket="test-bucket-mlops-lab9",
        prefix="models/models_lab_9/sentence_transformer.model/",
        local_dir="large_models/model/sentence_transformer.model",
    )
