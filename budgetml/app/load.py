import sys
from importlib import util
from importlib.machinery import SourceFileLoader
from tempfile import NamedTemporaryFile
from typing import Text, Type, Any

from google.cloud import storage


def import_class_from_source(source_path: Text, class_name: Text) -> Type[Any]:
    """Imports a class from a module provided as source file."""
    try:
        loader = SourceFileLoader(
            fullname='user_module',
            path=source_path,
        )
        spec = util.spec_from_loader(
            loader.name, loader, origin=source_path)
        module = util.module_from_spec(spec)
        sys.modules[loader.name] = module
        loader.exec_module(module)
        return getattr(module, class_name)
    except IOError:
        raise ImportError(
            '{} in {} not found in import_func_from_source()'.format(
                class_name, source_path))


def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    # bucket_name = "your-bucket-name"
    # source_blob_name = "storage-object-name"
    # destination_file_name = "local/path/to/file"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    print(
        "Blob {} downloaded to {}.".format(
            source_blob_name, destination_file_name
        )
    )


def get_predictor_class(path: Text, entrypoint: Text):
    assert path.startswith('gs://')
    bucket_name = path.replace('gs://', '').split('/')[0]
    source_blob_name = '/'.join(path.replace('gs://', '').split('/')[1:])

    # Download predictor
    with NamedTemporaryFile(suffix='.py') as temp_file:
        destination_file_name = temp_file.name
        download_blob(bucket_name, source_blob_name, destination_file_name)

        # Load class
        return import_class_from_source(destination_file_name, entrypoint)
