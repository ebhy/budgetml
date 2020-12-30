import logging
import os
import traceback
from typing import Type, Optional, Any

import uvicorn
from fastapi import Depends, FastAPI, File, UploadFile, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_401_UNAUTHORIZED

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

# globals
PREDICTOR: Optional[Any] = None
USERS_DB = {}

# auth
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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
    global USERS_DB

    # Setting auth creds
    USERS_DB = {
        'username': os.environ['BUDGET_USERNAME'],
        'password': os.environ['BUDGET_PWD'],
    }

    try:
        PREDICTOR_CLASS_PATH = os.getenv('BUDGET_PREDICTOR_PATH')
        assert PREDICTOR_CLASS_PATH is not None

        ENV_PREDICTOR_ENTRYPOINT = os.getenv('BUDGET_PREDICTOR_ENTRYPOINT',
                                             'Predictor')
        # Load predictor
        predictor_class: Type[Any] = get_predictor_class(
            PREDICTOR_CLASS_PATH, ENV_PREDICTOR_ENTRYPOINT)
        PREDICTOR = predictor_class()
        PREDICTOR.load()
    except Exception as e:
        logging.debug(f"Predictor class could not be loaded with: {str(e)}")
        traceback.print_exc()


@app.get("/")
def health_check():
    return {"I'm": "Alive!"}


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    global USERS_DB
    if form_data.username == USERS_DB['username'] \
            and form_data.password == USERS_DB['password']:
        return {
            "access_token": os.getenv('BUDGET_TOKEN'),
            "token_type": "bearer"
        }
    raise HTTPException(
        status_code=400, detail="Incorrect username or password")


@app.post("/predict/")
async def predict(request: Request,
                  _: str = Depends(verify)) -> Response:
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
                        _: str = Depends(verify)) -> Response:
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
                       _: str = Depends(verify)) -> Response:
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
    os.environ['BUDGET_USERNAME'] = 'username'
    os.environ['BUDGET_PWD'] = 'password'
    os.environ['BUDGET_TOKEN'] = 'token'
    uvicorn.run(app, host="0.0.0.0", port=8000)
