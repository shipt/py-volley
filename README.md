# Volley

Documentation: https://animated-guacamole-53e254cf.pages.github.io/

Provides an extensible Python interface to queue-like technologies with built in support for Kafka and [RSMQ](https://github.com/mlasevich/PyRSMQ) (Redis Simple Message Queue).

Use Volley if you need to quickly develop a Python streaming application to consumes messages, processes them (and do other things), then publish results to some place. Dead letters queues are easily configured.

[![Build Status](https://drone.shipt.com/api/badges/shipt/volley/status.svg)](https://drone.shipt.com/shipt/volley)
[![codecov](https://codecov.io/gh/shipt/volley/branch/main/graph/badge.svg?token=axP0uxJwPX)](https://codecov.io/gh/shipt/volley)

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

Volley applications, "workers", are implemented as a function decorated with an instance of the `volley.engine.Engine`. A component consumes from one queue and can publish to one or many queues.

A component function takes in `input_object` of type: `ComponentMessage`, which is a Pydantic model that accepts extra attributes. This model defines the schema of messages on the INPUT_QUEUE. The component function can process and modify that object to meet its needs.

Components output a list of tuples, where the tuple is defined as `(<name_of_queue>, ComponentMessage)`.
 The returned component message type must agree with the type accepted by the queue you are publishing to.

Below is a basic example that:
1) consumes from `input-topic` (a kafka topic).
2) evaluates the message from the queue
3) publishes a message to `output-topic` (also kafka topic)
4) Provides a path to a pydantic model that provides schema validation to both inputs and outputs.
5) Configures a dead-letter queue for any incoming messages that violate the specified schema.

```python
from typing import List, Tuple

from volley.engine import Engine
from volley.data_models import ComponentMessage

queue_config = {
    "input-topic": {
      "value": "stg.kafka.myapp.input",
      "type": "kafka",
      "schema": "example.data_models.InputMessage",  # for input validation
    },
    "output-topic": {
      "value": "stg.ds-marketplace.v1.my_kafka_topic_output",
      "type": "kafka",
      "schema": "example.data_models.OutputMessage",  # for output validation
    },
    "dead-letter-queue": {
      "value": "stg.kafka.myapp.dlq",
      "type": "kafka"
    }
}

engine = Engine(
  app_name="my_volley_app",
  input_queue="input-topic",
  output_queues=["output-topic"],
  dead_letter_queue="dead-letter-queue",
  queue_config=queue_config
)

@eng.stream_app
def hello_world(msg: InputMessage) -> List[Tuple[str, OutputMessage]]:
  if msg.value > 0:
    out_value = "foo"
  else:
    out_value = "bar"
  
  out = ComponentMessage(hello=out_value)

  return [("output-topic", out)]
```

Set environment variables for the Kafka connector:
```bash
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


## Another Example:

By default Volley will read queue configuration from a specified yaml. Let's define three queues, `my_input`, `queue_a`, `queue_b` and assume `my_input` is a Kafka topic populated by some external service. Let's decide that `queue_a` is an RSMQ type and `queue_b` is a Postgres. We define these in `./volley_config.yml`. Queues have `names`, which is how we reference them, and `values`. The engine interacts with the queue using the `value` and components (developers) interact with queue using the `name`.

Queues also have a schema. These are defined by subclassing `engine.data_models.ComponentMessage`. `ComponentMessage` are Pydantic models that accept extra attributes. This means if you do not provide a strictly subclass to a `ComponentMessage`, the message will get passed through to your component as key-value pairs from a `dict` of message on the queue, and constructed via `ComponentMessage(**message)`. The location of the data model for a queue is defined as the value of the `schema` attribute in the config file.

```yml
# ./volley_config.yml
queues:
  - name: my_input
    value: "stg.bus.kafka.topic.name"
    type: kafka
    schema: components.data_models.InputMessage
  - name: queue_a
    value: queue_a
    type: rsmq
    schema: components.data_models.MessageA
  - name: queue_b
    value: name_of_table
    type: rsmq
    schema: components.data_models.MessageA
```

Reminder: schemas for a queue are defined by subclassing `ComponentMessage`.

```python
# ./components/data_models.py
from engine.data_models import ComponentMessage

class InputMessage(ComponentMessage):
    list_of_values: List[float]


class MessageA(ComponentMessage):
    mean_value: float

class MessageB(ComponentMessage):
    max_value: float
```


## A multi-output example

`my_component_function` is implemented below. It consumes from `my_input` and publishes to `queue_a` and `queue_b` (defined above in `./volley_config.yml`).


```python
# my_components/my_component.py
engine = Engine(
  app_name="my_volley_app",
  input_queue="my_input",
  output_queues=["queue_a", "queue_b"]
)


@engine.stream_app
def my_component_function(input_object: ComponentMessage) -> List[(str, ComponentMessage)]
    """component function that computes some basics stats on a list of values
    
    Consumes from a queue named "my_input".
    Publishes to two queues, "queue_a", "queue_b"
    """

    # we can access the input models attributes like any other pydantic model
    mean_value = sum(input_object.list_of_values)/len(input_object.list_of_values)

    # or convert to a dict
    input_dict = input_object.dict()
    max_value = max(input_object["list_of_values"])

    # queue_a expects an object of type MessageA
    output_a = MessageA(mean_value=mean_value)

    # queue_b expects an object of type MessageB
    output_b = MessageB(max_value=max_value)

    # send the messages to the specificed queues
    return [
        ("queue_a", output_a),
        ("queue_b", output_b)
    ]
```

## No output example:

A component is not required to output anywhere. A typical use case would be if the component is filtering messages off a stream, and only producing if the message meets certain criteria. To do this, simply return `None` from the component function.


```python
from volley.engine import Engine


engine = Engine(
  app_name="my_volley_app",
  input_queue="my_input",
  output_queues=["queue_a"]
)


@engine.stream_app
def my_component_function(input_object: ComponentMessage) -> Optional[List[Tuple[str, ComponentMessage]]]:
    """component function that filters messages off a stream.
    
    Consumes from a queue named "my_input".
    Conditionally publishes to "queue_a" if the mean value is above 2
    """
    mean_value = sum(input_object.list_of_values)/len(input_object.list_of_values)

    if mean_value > 2:
      # queue_a expects an object of type MessageA
      output_a = MessageA(mean_value=mean_value)
      return [("queue_a", output_a)]
    else:
      return False
```

A component can also produce nothing.

```python
@engine.stream_app
def my_component_function(input_object: ComponentMessage) -> bool:
    print(input_object.list_of_values)
    return False
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

`make test.integration` Runs an "end-to-end" test against the example project in `./example`. The tests validate messages make it through all supported connectors and queues, plus a user defined connector plugin (postgres).


# Support

`#ask-machine-learning`
