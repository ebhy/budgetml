FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

COPY app /app
COPY requirements.txt requirements.txt
COPY app/gunicorn_conf.py /app/gunicorn_conf.py

RUN pip install -r requirements.txt