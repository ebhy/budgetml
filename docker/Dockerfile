FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

COPY ../budgetml/models /models
COPY ../budgetml/app /app
COPY ../budgetml/requirements.txt requirements.txt
COPY ../budgetml/gunicorn_conf.py ../gunicorn_conf.py

RUN pip install -r requirements.txt
