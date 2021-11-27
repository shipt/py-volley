# Volley

Forked from <a href="https://github.com/shipt/ml-bundle-engine">ml-bundle-engine</a>. Provides an extensible interface to queues with built in support for Kafka and <a href="https://github.com/shipt/ml-bundle-engine">Redis Simple Message Queue</a>. Use Volley if you need to quickly get up and running with a Python streaming application that consumes messages, processes them (and do other things), then publish results to some place. Dead letters queues are easily configured.

<p align="center">


</a> 


</a>
</p>


# Installation

1. Acquire creds to pypi.shipt.com #ask-machine-learning or #ask-info-sec

2. Export these to your shell 

```bash
export POETRY_HTTP_BASIC_SHIPT_USERNAME=your_username
export POETRY_HTTP_BASIC_SHIPT_PASSWORD=your_password
```

3. Install from pypi.shipt.com
```bash
pip install py-volley \
  --extra-index-url=https://${POETRY_HTTP_BASIC_SHIPT_USERNAME}:${POETRY_HTTP_BASIC_SHIPT_PASSWORD}@pypi.shipt.com/simple
```

## Getting started

Check out projects already using Volley:
  - [TLMD Future Route Actualizer](https://github.com/shipt/tlmd-future-route-actualizer) - Single worker that consumes from Kafka, does processing and invokes ML models, then publishes results to Kafka.
  - [Bundle Optimization Engine](https://github.com/shipt/ml-bundle-engine) - Collection of workers that consume/produce to Kafka, Redis, and Postgres. 

See also [additional documentation](./docs/../index.md)

Volley applications, "workers", are implemented as a function decorated with an instance of the `volley.engine.Engine`. A worker consumes from one queue and can publish to zero or many queues.

A worker function takes in input of type: `ComponentMessage`, which is a Pydantic model that accepts extra attributes. This model defines the schema of messages on the `input_queue`. The component function can process and modify that object to meet its needs.

Components output a list of tuples, where the tuple is defined as `(<name_of_queue>, ComponentMessage)`.
 The returned component message type must agree with the type accepted by the queue you are publishing to.

Below is a basic example that:
1) consumes from `input-topic` (a kafka topic).
2) evaluates the message from the queue
3) publishes a message to `output-topic` (also kafka topic)
4) Provides a path to a pydantic model that provides schema validation to both inputs and outputs.
5) Configures a dead-letter queue for any incoming messages that violate the specified schema or fail serialization.

```python
from typing import List, Tuple

from pydantic import BaseModel

from volley.engine import Engine


# define data models for the incoming and outgoing data
class InputMessage(BaseModel):
    """validate the incoming data"""

    list_of_values: List[float]


class OutputMessage(BaseModel):
    """validate the outgoing data"""

    max_value: float


# configure the Kafka topics
queue_config = {
    "input-topic": {
        "value": "incoming.kafka.topic",
        "type": "kafka",
        "schema": "data_models.InputMessage",
    },
    "output-topic": {
        "value": "outgoing.kafka.topic",
        "type": "kafka",
        "schema": "data_models.InputMessage",
    },
    # optionally - configure a dead-letter-queue
    "dead-letter-queue": {"value": "deadletter.kafka.topic", "type": "kafka"},
}

# intializae the Volley application
app = Engine(
    app_name="my_volley_app",
    input_queue="input-topic",
    output_queues=["output-topic"],
    dead_letter_queue="dead-letter-queue",
    queue_config=queue_config,
)


# decorate your function
@app.stream_app
def my_app(msg: InputMessage) -> List[Tuple[str, OutputMessage]]:
    max_value = msg.list_of_values
    output = OutputMessage(max_value=max_value)

    # send the output object to "output-topic"
    return [("output-topic", output)]

```

Set environment variables for the Kafka connector:
```
KAFKA_KEY=<kafka username>
KAFKA_SECRET=<kafka password>
KAFKA_BROKERS=<host:port of the brokers>
```

Alternatively, all consumer and producer configurations can be passed through to the connectors.
For reference
- [Kafka Configs](https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md)
```python
queue_config = {
    "input-topic": {
      "config": {  # configs to pass to kafka connector
        "group.id": "my-consumer-group",
        "bootstrap.servers": os.environ["KAFKA_BROKERS"],
        "sasl.username": os.environ["KAFKA_KEY"],
        "sasl.password": os.environ["KAFKA_SECRET"],
      },
      "value": "stg.kafka.myapp.input",
      "type": "kafka",
      "schema": "example.data_models.InputMessage",
    },
```

## No output example:

A component is not required to output anywhere. A typical use case would be if the component is filtering messages off a stream, and only producing if the message meets certain criteria. To do this, simply return `None` from the component function.

```python
from random import randint
@engine.stream_app
def my_component_function(input_object: InputMessage) -> Optional[List[Tuple[str, OutputMessage]]]:
  rando = randint(0, 100)
  if rando > 50:
    return None
  else:
    msg = OutputMessage(my_msg="hello")
    return [("output-topic", msg)]
```

## Running a worker component
Components are run as stand-alone workers.

```python
# main.py
from my_components import my_component_function
my_component_function()
```

And are run by invoking the function.
```bash
python main.py
```

# CI / CD

See `.drone.yml` for test gates. A Semantic tagged release triggers a build and publish to pypi.shipt.com.

# Testing

`make test.unit` Runs unit tests on individual components with mocked responses dependencies external to the code. Docker is not involved in this process.

`make test.integration` Runs an "end-to-end" test against the example project in `./example`. The tests validate messages make it through all supported connectors and queus, plus a user defined connector plugin (postgres).

# Support

`#ask-machine-learning`
