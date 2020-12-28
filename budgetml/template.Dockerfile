FROM $BASE_IMAGE

COPY custom_requirements.txt custom_requirements.txt

RUN pip install -r custom_requirements.txt