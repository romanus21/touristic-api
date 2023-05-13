FROM python:3.9-slim

RUN mkdir /project
WORKDIR /project

COPY . /project

RUN apt-get install build-essentials

RUN pip install -r requirements.txt


ENTRYPOINT ["/project/app/main.py"]