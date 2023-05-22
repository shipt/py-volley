FROM python:3.9

WORKDIR /app

COPY . .

RUN pip3 install poetry==1.4.2
RUN poetry config virtualenvs.create false
RUN poetry install --no-root -E all
