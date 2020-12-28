import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict

import cv2
import numpy as np
from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response, FileResponse
from tensorflow import keras

from budgetml.app.predictor import Predictor


def check_size(img):
    # check size
    if img.shape[0] > 1500 or img.shape[1] > 1500:
        return False
    return True


class FastSRGANPredictor(Predictor):
    def __init__(self, args: Dict):
        super().__init__(args)
        # Fast model
        t = Path(os.path.abspath(__file__)).parent.parent
        path_to_model = str(t / 'models' / 'fastsrgan' / 'generator.h5')
        fast_model = keras.models.load_model(path_to_model)
        inputs = keras.Input((None, None, 3))
        output = fast_model(inputs)
        self.model = keras.models.Model(inputs, output)

    async def predict(self, request: Request) -> Response:
        contents = await request.file.read()
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
