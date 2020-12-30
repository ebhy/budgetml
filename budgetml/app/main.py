import logging
import os
import traceback
from typing import Type, Optional

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from basepredictor import BasePredictor
from load import get_predictor_class
from models import Payload

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# predictor
PREDICTOR: Optional[BasePredictor] = None


@app.on_event("startup")
async def startup_event():
    global PREDICTOR

    try:
        PREDICTOR_CLASS_PATH = os.getenv('BUDGET_PREDICTOR_PATH')
        assert PREDICTOR_CLASS_PATH is not None

        ENV_PREDICTOR_ENTRYPOINT = os.getenv('BUDGET_PREDICTOR_ENTRYPOINT',
                                             'Predictor')
        # Load predictor
        args = {}
        predictor_class: Type[BasePredictor] = get_predictor_class(
            PREDICTOR_CLASS_PATH, ENV_PREDICTOR_ENTRYPOINT)
        PREDICTOR = predictor_class(args)
    except Exception as e:
        logging.debug(f"Predicto class could not be loaded with: {str(e)}")
        traceback.print_exc()


@app.get("/")
def health_check():
    return {"I'm": "Alive!"}


@app.post("/predict/")
async def predict(request: Request) -> Response:
    global PREDICTOR
    if PREDICTOR is None:
        raise HTTPException(
            status_code=400,
            detail="The predictor could not be loaded. Please check the logs "
                   "for more detail.",
        )
    return await PREDICTOR.predict(request)


@app.post("/predict_image/")
async def predict_image(request: UploadFile = File(...)) -> Response:
    """
    https://fastapi.tiangolo.com/tutorial/request-files/

    :param request:
    :return:
    """
    global PREDICTOR
    if PREDICTOR is None:
        raise HTTPException(
            status_code=400,
            detail="The predictor could not be loaded. Please check the logs "
                   "for more detail.",
        )
    return await PREDICTOR.predict(request)


@app.post("/predict_dict/")
async def predict_dict(request: Payload) -> Response:
    """
    Request is Payload type which has a dict.

    :param request:
    :return:
    """
    global PREDICTOR
    if PREDICTOR is None:
        raise HTTPException(
            status_code=400,
            detail="The predictor could not be loaded. Please check the logs "
                   "for more detail.",
        )
    return await PREDICTOR.predict(request)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
