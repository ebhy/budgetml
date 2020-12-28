from typing import Type

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from budgetml.app.predictor import Predictor

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load predictor
args = {}
predictor_class: Type[Predictor] = get_predictor_class()
predictor = predictor_class(args)


@app.get("/")
def health_check():
    return {"I'm": "Alive!"}


@app.post("/predict/")
async def predict(request: Request) -> Response:
    return predictor.predict(request)
