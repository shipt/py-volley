FROM python:3.9.4 as base

WORKDIR /app

COPY poetry.lock pyproject.toml /app/

RUN pip3 install poetry==1.1.11

RUN poetry config virtualenvs.create false

FROM base as dev
RUN poetry install --no-root
COPY . /app/
