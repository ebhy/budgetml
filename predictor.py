from typing import Dict

from starlette.requests import Request
from starlette.responses import Response


class MyPredictor:
    def __init__(self, args: Dict):
        pass

    def predict(self, request: Request) -> Response:
        return Response('WOW')
