
FROM python:3.9.4

ARG SHIPT_PYPI_USERNAME
ARG SHIPT_PYPI_PASSWORD

ENV POETRY_HTTP_BASIC_SHIPT_USERNAME=$SHIPT_PYPI_USERNAME
ENV POETRY_HTTP_BASIC_SHIPT_PASSWORD=$SHIPT_PYPI_PASSWORD

WORKDIR /app

COPY poetry.lock pyproject.toml /app/

RUN pip3 install poetry==1.1.11

RUN poetry config virtualenvs.create false \
    &&  poetry install --no-dev

COPY . /app/
