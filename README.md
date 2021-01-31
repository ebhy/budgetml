# BudgetML
Deploy your model in production on a budget in less than 10 lines of code.

BudgetML lets you deploy your model on a spot/preemtible instance (which is ~80% cheaper than a regular instance) with a secured, HTTPS API endpoint.
The tool sets it up in a way that the instance autostarts when it shuts down (at least once every 24 hours) with only a few minutes of downtime.

BudgetML gives ensures the cheapest possible API endpoint with the lowest possible downtime. Therefore, it is aimed at 
## Key Features
* 
## Quickstart
BudgetML aims for as simple a process as possible. First set up a predictor:

```python
# predictor.py
class Predictor:
    def load(self):
        from transformers import pipeline
        self.model = pipeline(task="sentiment-analysis")

    async def predict(self, request):
        # We know we are going to use the `predict_dict` method, so we use
        # the request.payload pattern
        req = request.payload
        return self.model(req["text"])[0]
```

Then launch it with a simple script:
```python
# deploy.py
import budgetml
from predictor import Predictor

# add your GCP project name here.
budgetml = budgetml.BudgetML(project='GCP_PROJECT')

# launch endpoint
budgetml.launch(
    Predictor,
    domain="example.com",
    subdomain="api",
    static_ip="32.32.32.322",
    machine_type="e2-medium",
    requirements=['tensorflow==2.3.0', 'transformers'],
)
```
For a deeper dive, [check out the detailed guide](examples/deploy_simple_model) in the [examples](examples) directory. For 
more information about the BudgetML API, refer to the [docs](docs).

## Projects using BudgetML
[PicHance](https://pichance.com)
[you-tldr](https://you-tldr.com)

## ZenML: For more production-scenarios
BudgetML is for users on a budget. If you're working in a more serious production environment, then consider using 
[ZenML](https://github.com/maiot-io/zenml) as the perfect open-source MLOPs framework for ML production needs. It does 
more than just deployments, and is more suited for professional workplaces.

## Proudly built by two brothers
We are two brothers who love building products.
