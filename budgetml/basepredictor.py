from abc import abstractmethod
from typing import Union, Any

from fastapi import UploadFile
from starlette.requests import Request
from starlette.responses import Response


class BasePredictor:
    def load(self):
        """Called once during each worker initialization. Performs
        setup such as downloading/initializing the model or downloading a
        vocabulary.
        """
        pass

    @abstractmethod
    async def predict(self,
                      request: Union[
                          Request, UploadFile, Any]) -> Response:
        """Responsible for running the inference.

        Args:
            request (required): The request from the server client
        """
        pass
