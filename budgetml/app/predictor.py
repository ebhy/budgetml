from abc import abstractmethod
from typing import Dict

from starlette.requests import Request
from starlette.responses import Response


class Predictor:
    def __init__(self, args: Dict):
        """Called once during each worker initialization. Performs
        setup such as downloading/initializing the model or downloading a
        vocabulary.

        Args:
            args (required): Dictionary which contains args
        """
        pass

    @abstractmethod
    def predict(self, request: Request) -> Response:
        """Responsible for running the inference.

        Args:
            request (required): The request from the server client

        Returns:

        """
        pass
