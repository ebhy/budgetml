FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim

COPY budgetml/app /app
COPY requirements.txt requirements.txt
COPY gunicorn_conf.py ../gunicorn_conf.py

RUN pip install -r requirements.txt
