FROM python:3.8 as build

WORKDIR /app

RUN python3 -m venv venv
ENV PATH="/app/venv/bin:$PATH"

COPY ./requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

COPY ./src ./src
COPY ./tests ./tests

RUN pytest


FROM python:3.8-slim

WORKDIR /app

COPY --from=build /app/venv ./venv
ENV PATH="/app/venv/bin:$PATH"

COPY ./src ./src

CMD uvicorn src.main:app --host 0.0.0.0 --port $PORT
