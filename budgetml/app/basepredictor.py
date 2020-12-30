from abc import abstractmethod
from typing import Dict, Union

from fastapi import UploadFile
from starlette.requests import Request
from starlette.responses import Response

from models import Payload


class BasePredictor:
    def load(self):
        """Called once during each worker initialization. Performs
        setup such as downloading/initializing the model or downloading a
        vocabulary.

        Args:
            args (required): Dictionary which contains args
        """
        pass

    @abstractmethod
    async def predict(self,
                      request: Union[
                          Request, UploadFile, Payload]) -> Response:
        """Responsible for running the inference.

        Args:
            request (required): The request from the server client

        Returns:

        """
        pass
