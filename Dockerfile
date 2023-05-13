FROM python:3.9-alpine

RUN mkdir /project
WORKDIR /project

COPY . /project

RUN apk add build-essential

RUN apk update && apk add python3-dev \
                          gcc \
                          libc-dev \
                          libffi-dev

RUN pip install -r requirements.txt


ENTRYPOINT ["/project/app/main.py"]