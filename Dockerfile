FROM python:3.9

ENV LIBRDKAFKA_VER=1.9.0

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

COPY . .

RUN pip3 install poetry==1.4.2
RUN poetry config virtualenvs.create false
RUN poetry install --no-root -E all
