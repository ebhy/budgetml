class Predictor:
    def load(self):
        from transformers import pipeline
        self.model = pipeline(task="sentiment-analysis")

    async def predict(self, request):
        # We know we are going to use the `predict_dict` method, so we use
        # the request.payload pattern
        req = request.payload
        return self.model(req["text"])[0]
