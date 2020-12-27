import os
import shutil
import tempfile
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from tensorflow import keras
from pathlib import Path

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Fast model
t = Path(os.path.abspath(__file__)).parent.parent
path_to_model = str(t / 'models'/ 'fastsrgan'/ 'generator.h5')
fast_model = keras.models.load_model(path_to_model)
inputs = keras.Input((None, None, 3))
output = fast_model(inputs)
fast_model = keras.models.Model(inputs, output)

origins = ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "Hancers!"}


def check_size(img):
    # check size
    if img.shape[0] > 1500 or img.shape[1] > 1500:
        return False
    return True


async def resize(img_np):
    low_res = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
    low_res = low_res / 255.0
    sr = fast_model.predict(np.expand_dims(low_res, axis=0))[0]
    sr = ((sr + 1) / 2.) * 255
    sr = cv2.cvtColor(sr, cv2.COLOR_RGB2BGR)
    return sr


@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.fromstring(contents, np.uint8)
    img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if not check_size(img_np):
        raise HTTPException(
            status_code=400,
            detail="Image is too large with shape {}x{}".format(
                img_np.shape[0], img_np.shape[1]),
        )

    try:
        sr = await resize(img_np)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="The ML model failed! The error is {}".format(str(e)),
        )

    # we need to delete tmp dir everytime. hacky
    tmp_dir = 'tmp_fast'
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.mkdir(tmp_dir)
    with tempfile.NamedTemporaryFile(mode="w+b", dir=tmp_dir, suffix=".png",
                                     delete=False) as f:
        cv2.imwrite(f.name, sr)
        return FileResponse(f.name, media_type="image/png")
