FROM python:3.9-alpine

RUN mkdir /project
WORKDIR /project

COPY . /project

RUN apk --update add --virtual build-dependencies libffi-dev openssl-dev python-dev py-pip build-base \
  && pip install --upgrade pip \
  && pip install -r requirements.txt \
  && apk del build-dependencies

ENTRYPOINT ["/project/app/main.py"]