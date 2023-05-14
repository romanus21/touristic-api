FROM python:3.9-slim

RUN mkdir /project
WORKDIR /project

COPY ./requirements.txt /project

RUN apt-get update \
    && apt-get install gcc -y \
    && apt-get clean

RUN pip install -r requirements.txt

COPY ./app /project/app
COPY ./envs /project/app

RUN chmod +x /project/app/main.py

ENV PYTHONPATH="${PYTHONPATH}:/project/app"

ENTRYPOINT ["python", "/project/app/main.py"]