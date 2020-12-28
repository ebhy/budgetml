import logging

from google.cloud import storage
from google.cloud.exceptions import Conflict


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    logging.debug(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )


def create_bucket_if_not_exists(bucket_name):
    """Create a new bucket in specific location"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    try:
        new_bucket = storage_client.create_bucket(bucket, location="us")
        logging.debug(
            "Created bucket {} in {} with storage class {}".format(
                new_bucket.name, new_bucket.location, new_bucket.storage_class)
        )
        return new_bucket
    except Conflict:
        logging.debug(
            "Bucket {} in {} already exists".format(
                bucket.name, bucket.location))
        return bucket
