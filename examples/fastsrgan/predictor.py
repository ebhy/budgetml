import os
import shutil
import tempfile

import cv2
import numpy as np
from fastapi import HTTPException
from fastapi import UploadFile, File
from google.cloud import storage
from starlette.responses import Response, FileResponse
from tensorflow import keras


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


def check_size(img):
    # check size
    if img.shape[0] > 1500 or img.shape[1] > 1500:
        return False
    return True


class FastSRGANPredictor:
    def load(self):
        # Fast model
        with tempfile.NamedTemporaryFile() as f:
            # TODO: BILAL POINT THIS TO THE RIGHT BUCKET AND MODEL
            # download_blob('budget_models', 'fastsrgan/generator.h5', f.name)
            fast_model = keras.models.load_model(f.name)
            inputs = keras.Input((None, None, 3))
            output = fast_model(inputs)
            self.model = keras.models.Model(inputs, output)

    async def predict(self, request: UploadFile = File(...)) -> Response:
        contents = await request.read()
        nparr = np.fromstring(contents, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if not check_size(img_np):
            raise HTTPException(
                status_code=400,
                detail="Image is too large with shape {}x{}".format(
                    img_np.shape[0], img_np.shape[1]),
            )

        low_res = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
        low_res = low_res / 255.0
        sr = self.model.predict(np.expand_dims(low_res, axis=0))[0]
        sr = ((sr + 1) / 2.) * 255
        sr = cv2.cvtColor(sr, cv2.COLOR_RGB2BGR)

        # we need to delete tmp dir everytime. hacky
        tmp_dir = 'tmp_fast'
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.mkdir(tmp_dir)
        with tempfile.NamedTemporaryFile(mode="w+b", dir=tmp_dir,
                                         suffix=".png",
                                         delete=False) as f:
            cv2.imwrite(f.name, sr)
            return FileResponse(f.name, media_type="image/png")
