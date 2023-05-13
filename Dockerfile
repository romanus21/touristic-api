FROM python:3.9-slim

RUN mkdir /project
WORKDIR /project

COPY . /project

RUN pip install -r /project/requirements.txt

ENTRYPOINT ["/project/app/main.py"]