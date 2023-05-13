FROM python:3.9-slim

RUN mkdir /project
WORKDIR /project

COPY . /project

RUN apk update && apk add python3-dev \
                          gcc \
                          libc-dev \
                          libffi-dev

RUN pip install -r requirements.txt \


ENTRYPOINT ["/project/app/main.py"]