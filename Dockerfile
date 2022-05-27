FROM python:3.9.4 as base

ARG ARTIFACTORY_PYPI_USERNAME
ARG ARTIFACTORY_PYPI_PASSWORD

ENV POETRY_HTTP_BASIC_SHIPT_RESOLVE_USERNAME=$ARTIFACTORY_PYPI_USERNAME
ENV POETRY_HTTP_BASIC_SHIPT_RESOLVE_PASSWORD=$ARTIFACTORY_PYPI_PASSWORD
ENV LIBRDKAFKA_VER=1.8.2

RUN apt-get update && \
    apt-get install -y \
    libpq-dev \
    libssl-dev \ 
    libzmq3-dev \
    python3-dev

ENV KAFKA_DIR=/usr/local
WORKDIR $KAFKA_DIR
RUN wget https://github.com/edenhill/librdkafka/archive/refs/tags/v$LIBRDKAFKA_VER.tar.gz  -O - | tar -xz
WORKDIR $KAFKA_DIR/librdkafka-$LIBRDKAFKA_VER
RUN ./configure --prefix=$KAFKA_DIR \
    && make \
    && make install \
    && ldconfig
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$KAFKA_DIR/lib


WORKDIR /app

COPY poetry.lock pyproject.toml /app/

RUN pip3 install poetry==1.1.11

RUN poetry config virtualenvs.create false

FROM base as dev

RUN poetry install --no-root -E all
COPY . /app/
