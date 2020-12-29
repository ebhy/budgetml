import os
from typing import Type, Optional

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from basepredictor import BasePredictor
from load import get_predictor_class

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

    PREDICTOR_CLASS_PATH = os.getenv('BUDGET_PREDICTOR_PATH')
    assert PREDICTOR_CLASS_PATH is not None

    ENV_PREDICTOR_ENTRYPOINT = os.getenv('BUDGET_PREDICTOR_ENTRYPOINT',
                                         'Predictor')
    # Load predictor
    args = {}
    predictor_class: Type[BasePredictor] = get_predictor_class(
        PREDICTOR_CLASS_PATH, ENV_PREDICTOR_ENTRYPOINT)
    PREDICTOR = predictor_class(args)


@app.get("/")
def health_check():
    return {"I'm": "Alive!"}


@app.post("/predict/")
async def predict(request: Request) -> Response:
    global PREDICTOR
    return await PREDICTOR.predict(request)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
