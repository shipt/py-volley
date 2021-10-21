# ML Bundle Engine
The ML bundle engine is an event driven series of processes & queues. 
The engine intakes a Kafka message from the bundle request topic, makes a prediction with an ML model, runs an optimizer and outputs to a Kafka topic.

[![Build Status](https://drone.shipt.com/api/badges/shipt/ml-bundle-engine/status.svg)](https://drone.shipt.com/shipt/ml-bundle-engine)

## Maintainer(s)
 - @Jason
 - @AdamH

## Run locally
1. Acquire creds to pypi.shipt.com #ask-machine-learning

2. Export these to your shell

```bash
export POETRY_HTTP_BASIC_SHIPT_USERNAME=your_username
export POETRY_HTTP_BASIC_SHIPT_PASSWORD=your_password
```

3. Ensure [docker](https://docs.docker.com/get-docker/) is installed in your local environment.

Start all services and data stores:

`make run` - this spins up all the components listed below along with local instances of Kafka, Redis, and Postgres all running in Docker.

- dummy_events: components/dummy_events.py - produces dummy kafka messages to an `input-topic` kafka
- features: components/feature_generator.py - reads from `input-topic` kafka, publishes to `triage` queue
- triage: components/triage.py - reads from `triage` queue, publishes to `optimizer` queue
- optimizer: components/optimizer.py - reads from `optimizer` queue, publishes to `collector` or back to `optimizer` queue
- fallback: components/fallback.py - reads from `fallback` queue, publishes to `collector` queue
- collector: components/collector.py - reads from `collector` queue and publishes to `publisher` table in postgres
- publisher: components/publisher.py - reads from the `publisher` table in postgre and produces to `output-topic` kafka
- dummy_consumer: components/dummy_consimer.py - reads from `output-topic` kafka and logs to stddout

Stop all services and data stores
`make stop`

## Simulating Staging Data

- `make notebook` will spin up jupyer notebook. Open `./notebooks/publish_consume.ipynb`. Publish messages to the input topic and then consume data from the output topic. You will need to acquire Kafka credentials from your team in order to publish and consume from Kafka.
