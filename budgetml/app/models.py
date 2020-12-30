from typing import Dict

from pydantic import BaseModel


class Payload(BaseModel):
    payload: Dict = {}
