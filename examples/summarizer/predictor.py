from typing import Dict

import torch
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.responses import Response
from transformers import PegasusForConditionalGeneration, PegasusTokenizer


class Payload(BaseModel):
    payload: Dict = {}


class Predictor:
    def load(self):
        # Fast model
        self.model_name = 'google/pegasus-xsum'
        self.torch_device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.tokenizer = PegasusTokenizer.from_pretrained(self.model_name)
        self.model = PegasusForConditionalGeneration.from_pretrained(
            self.model_name).to(self.torch_device)

    async def predict(self, request: Payload) -> Response:
        req = request.payload
        source_txt = req['text']

        # defaults
        num_beams = req['num_beams'] if 'num_beams' in req else 4
        min_length = req['min_length'] if 'min_length' in req else 32
        max_length = req['max_length'] if 'max_length' in req else 64
        padding = req['padding'] if 'padding' in req else 'longest'
        truncation = req['truncation'] if 'truncation' in req else True

        batch = self.tokenizer.prepare_seq2seq_batch(
            source_txt,
            truncation=truncation,
            padding=padding,
            return_tensors="pt").to(self.torch_device)
        translated = self.model.generate(
            **batch,
            num_beams=num_beams,
            min_length=min_length,
            max_length=max_length)
        tgt_text = self.tokenizer.batch_decode(
            translated,
            skip_special_tokens=True)
        return JSONResponse(content={'output': tgt_text})
