# Technical Overview
There are no full-fledged docs (yet), so this page serves as the single source of truth of all the technical nuances required 
to get most projects off the ground. If your question is still not covered here, feel free to open an issue and ask.

## Predictor
The predictor class is where the logic of the model inference is placed. The user can call it whatever they want. It does not 
need to inherit from anything. It just needs to be a simple python class, with two functions `load` and `predict`. The definitions 
of these functions can be found [here](../../budgetml/budgetml/basepredictor.py). Briefly:

```python
class Predictor:
    def load(self):
        """Called once during each worker initialization. Performs
        setup such as downloading/initializing the model or downloading a
        vocabulary.
        """
        pass

    @abstractmethod
    async def predict(self,
                      request: Union[Request, UploadFile, Any]) -> Response:
        """Responsible for running the inference.

        Args:
            request (required): The request from the server client
        """
        pass
```
The `request` parameter in `predict` is a FastAPI [Request](https://fastapi.tiangolo.com/advanced/using-request-directly/) object. Read the [Server](#server) 
section below to understand how to manage it.

## Launch (what does it do)
The `budgetml.launch()` triggers the following sequence of events:

* Creates a Google Cloud Bucket and uploads the specified `Predictor` class definition to it, to be accessed by the VM.
* Spins up the preemtible VM with a startup script that has all details to spin up the server and issue the SSL certificate.
* Exposes the API to a public facing port 80.
* Creates a Google Scheduler Job that triggers a Google Cloud Function via Pub/Sub every minute (or specified schedule). 
  This function constantly attempts to start the VM each time.

## Launch locally
The `budgetml.launch_local()` simulates all of the above locally. This is for testing purposes.

## Server
The server is a simple [FastAPI](https://fastapi.tiangolo.com/) server. The entire server can be found [here](../server/app). While the 
server is very basic, it is still important to understand its components. Here they are:

* It uses [gunicorn](https://gunicorn.org/) under-the-hood to serve requests.
* It has three environment variables that it utilizes, namely `BUDGET_USERNAME`, `BUDGET_PWD`, `BUDGET_TOKEN`, which are all passed in the startup script on VM creation.
* It uses the [startup_event](https://fastapi.tiangolo.com/advanced/events/) hook to do predictor.load() at the very start of the server initialization.
* It uses the [Password and Bearer pattern](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/) for OAuth2 authorization.
* Apart from the OAuth endpoints, it has three different endpoints to be used for various ML use-cases. These endpoints are closely tried to the `Predictor` class that is passed, and 
the `Predictor` class should have baked-in knowledge of what endpoint is to be hit after deployment. Here is more information about these endpoints:

### Generic (`/predict`)
The Generic endpoint (`/predict`) is meant for the most general-purpose use-case. 
### Dict (`/predict_dict`)
The Dict endpoint (`/predict_dict`) is meant for use-case where the input to the model can be represented as a JSON-style dict object.

### Image (`/predict_image`)
The Image endpoint (`/predict_image`) is meant for the use-case where the input to the model can be represented as an image.

## Server Environment
The `launch` method takes an optional list of python requirements. After launch, the startup script executes a series of steps including:

* Pulling a specified docker image (defaults to BudgetML public default image, e.g., `us.gcr.io/budgetml/budgetml:base-0.1.0`)
* Installs everything specified in the `requirements` argument.
* Runs the server.

Therefore, the user can either just specify their own requirements, or create a custom Docker image based on the server base image, whose 
Dockerfile can be found [here](../server/Dockerfile).