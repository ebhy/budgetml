from typing import Dict

from starlette.requests import Request
from starlette.responses import Response

from budgetml import BasePredictor


class MyPredictor(BasePredictor):
    def __init__(self, args: Dict):
        super().__init__(args)

    def predict(self, request: Request) -> Response:
        return Response('WOW')
