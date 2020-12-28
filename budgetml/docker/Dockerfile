FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

COPY ../models /models
COPY ../app /app
COPY ../budgetml/requirements.txt requirements.txt
COPY ../gunicorn_conf.py ../gunicorn_conf.py

RUN pip install -r requirements.txt
