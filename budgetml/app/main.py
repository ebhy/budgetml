import logging
import os
import traceback
from typing import Type, Optional

import uvicorn
from fastapi import Depends, FastAPI, File, UploadFile, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_401_UNAUTHORIZED

from basepredictor import BasePredictor
from load import get_predictor_class
from models import Payload, User

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

# auth
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
users_db = {
    "username": "johndoe",
    "full_name": "John Doe",
    "email": "johndoe@example.com",
    "hashed_password": "fakehashedsecret",
    "disabled": False,
}


def fake_decode_token(token):
    return User(
        username=token + "fakedecoded", email="john@example.com",
        full_name="John Doe"
    )


async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    return user


async def verify(token: str = Depends(oauth2_scheme)):
    try:
        if token == os.getenv('BUDGET_TOKEN'):
            return token
        raise Exception
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials with error {}".format(
                str(e)),
            headers={"WWW-Authenticate": "Bearer"},
        )


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


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400,
                            detail="Incorrect username or password")
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400,
                            detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}


@app.post("/predict/")
async def predict(request: Request,
                  _: str = Depends(get_current_user)) -> Response:
    global PREDICTOR
    if PREDICTOR is None:
        raise HTTPException(
            status_code=400,
            detail="The predictor could not be loaded. Please check the logs "
                   "for more detail.",
        )
    return await PREDICTOR.predict(request)


@app.post("/predict_image/")
async def predict_image(request: UploadFile = File(...),
                        _: str = Depends(get_current_user)) -> Response:
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
async def predict_dict(request: Payload,
                       _: str = Depends(get_current_user)) -> Response:
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
