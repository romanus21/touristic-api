FROM python:3.9-slim

RUN mkdir /project
WORKDIR /project

COPY ./requirements.txt /project

RUN apt-get update \
    && apt-get install gcc -y \
    && apt-get clean

RUN pip install -r requirements.txt

COPY ./app /project/app

RUN chmod +x /project/app/main.py

ENTRYPOINT ["python3", "/project/app/main.py"]