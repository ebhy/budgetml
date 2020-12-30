# BudgetML
Deploy your model in production for less than $20/month with less than 20 lines of code.
BudgetML lets you deploy your model on a preemptible instance (which is ~70% cheaper than a regular instance) with a https API endpoint.
We autostart the instance when it shuts down so your instance only goes down for 1-2 minutes before its up again.

# Setup

## Install
```bash
pip install budgetml
```

## Create GCP Project
Create a GCP project

## Create Service Account
We use Google Cloud under the hood. Make sure you have created a GCP project before proceeding.
Also have your Google Credentials service account file available.

The most convenient way is through the gcloud command line. 
For convenience:
Run the following commands to avoid retyping:
export PROJECT_ID=<enter your Google Cloud Project name>
export SA_NAME="sa-name"
export SA_PATH="$(pwd)/sa.json"

##### Creating the actual Service Account
```bash
gcloud iam service-accounts create ${SA_NAME}
```

#### Creating a json-key for the new Service Account
```bash
gcloud iam service-accounts keys create ${SA_PATH} \
    --iam-account ${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
```

#### Give permissions to the new Service Account
```bash
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member=serviceAccount:${SA_NAME}@${PROJECT_ID}.gserviceaccount.com \
    --role "roles/editor" 
```

## Enable APIs

You need to enable APIs. We need

* Compute Engine
* Google Cloud Functions [For this we need Cloud Build]

## Create Predictor
Create a a BasePredictor class

```python
class BasePredictor:
    def load(self):
        """Called once during each worker initialization. Performs
        setup such as downloading/initializing the model or downloading a
        vocabulary.
        """
        pass

    async def predict(self, request) -> Response:
        """Responsible for running the inference.

        Args:
            request (required): The request from the server client
        """
        pass
```

## Create Static IP Address
```python
import budgetml
budgetml = budgetml.BudgetML(project='YOUR_PROJECT')
IP_ADDRESS = budgetml.create_static_ip('STATIC-IP-NAME')
print(IP_ADDRESS)
```

## Create A record
Add an A record that points your subdomain.domain to IP_ADDRESS.

## Launch Instance
Time to launch! Just a few lines of code between your model and live API :)

```python
import budgetml
import Predictor

# create BudgetML instance. Add your GCP project name here.
budgetml = budgetml.BudgetML(project='YOUR_PROJECT')

# launch instance
budgetml.launch(
    Predictor,
    domain="example.com",
    subdomain="api",
    requirements_path='path/to/fastsrgan_requirements.txt',
    static_ip=IP_ADDRESS
)
```

And that's it!