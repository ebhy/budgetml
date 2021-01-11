from typing import Dict

import firebase_admin
import torch
from fastapi.responses import JSONResponse
from firebase_admin import firestore
from pydantic import BaseModel
from starlette.responses import Response
from transformers import PegasusForConditionalGeneration, PegasusTokenizer


if not firebase_admin._apps:
    firebase_admin.initialize_app()
db = firestore.client()


class Payload(BaseModel):
    payload: Dict = {}


def get_transcript_data(collection, doc_id):
    print(f"get_transcript_data {collection}:{doc_id}")
    return db.collection(collection).document(
        doc_id).get().to_dict()['transcriptData']


def get_transcript(transcript_data, transcript_language='en'):
    transcript = [
        x for x in transcript_data
        if x['transcriptLanguageCode'].startswith(
            transcript_language)][0]['transcript']
    d = " ".join([x['text'] for x in transcript])
    print(f"Transcript: {d}")
    return d


def update_transcript(collection, doc_id, summary, transcript_language='en'):
    print(
        f"update_transcript {collection}:{doc_id}:{summary}:"
        f"{transcript_language}")
    new_transcript_data = get_transcript_data(collection, doc_id)
    for transcript_info in new_transcript_data:
        if transcript_info['transcriptLanguageCode'].startswith(
                transcript_language):
            transcript_info['transcriptSummary'] = summary
    print(f"new transcript list: {new_transcript_data}")
    db.collection(collection).document(doc_id).update(
        {u'transcriptData': new_transcript_data})

    # analytics
    res = db.collection(u'analytics').limit(1).get()[0]
    db.collection(u'analytics').document(res.id).update({
        'transcriptSummarize': firestore.Increment(1),
    })


class Predictor:
    def __init__(self):
        self.transcript_language = None
        self.update_doc = True
        self.collection = u'videos'
        self.num_beams = None
        self.min_length = None
        self.max_length = None
        self.padding = None
        self.truncation = None
        self.chunk_size = 512

    def load(self):
        # Fast model
        self.model_name = 'google/pegasus-xsum'
        self.torch_device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.tokenizer = PegasusTokenizer.from_pretrained(self.model_name)
        self.model = PegasusForConditionalGeneration.from_pretrained(
            self.model_name).to(self.torch_device)

    def get_summary(self, source_txt):
        batch = self.tokenizer.prepare_seq2seq_batch(
            [source_txt],
            truncation=self.truncation,
            padding=self.padding,
            return_tensors="pt").to(self.torch_device)
        translated = self.model.generate(
            **batch,
            num_beams=self.num_beams,
            min_length=self.min_length,
            max_length=self.max_length)
        return self.tokenizer.batch_decode(
            translated,
            skip_special_tokens=True)

    async def predict(self, request: Payload) -> Response:
        req = request.payload
        doc_id = req['doc_id']

        # defaults
        self.transcript_language = req[
            'transcript_language'] if 'transcript_language' in req else 'en'
        self.update_doc = req['update_doc'] if 'update_doc' in req else True
        self.collection = req[
            'collection'] if 'collection' in req else u'videos'
        self.num_beams = req['num_beams'] if 'num_beams' in req else 2
        self.min_length = req['min_length'] if 'min_length' in req else 32
        self.max_length = req['max_length'] if 'max_length' in req else 64
        self.padding = req['padding'] if 'padding' in req else 'longest'
        self.truncation = req['truncation'] if 'truncation' in req else True
        self.chunk_size = req['chunk_size'] if 'chunk_size' in req else 512

        # get firestore data
        transcript_data = get_transcript_data(self.collection, doc_id)
        transcript = get_transcript(transcript_data, self.transcript_language)

        summary = ''
        n = self.chunk_size
        transcript = transcript.split(" ")
        for txt_list in \
                [transcript[i:i + n] for i in range(0, len(transcript), n)]:
            txt = " ".join(txt_list)
            new_summary = self.get_summary(txt)[0]
            print(f"Part summary: {new_summary}")
            summary += new_summary + '. '
        print(f"Overall summary: {summary}")

        if self.update_doc:
            # update firestore
            update_transcript(self.collection, doc_id, summary,
                              self.transcript_language)
        return JSONResponse(content={'output': summary})
