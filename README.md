[![Build Status](https://drone.shipt.com/api/badges/shipt/volley/status.svg?ref=refs/heads/main)](https://drone.shipt.com/shipt/volley)

Forked from https://github.com/shipt/ml-bundle-engine. Provides an extensible interface to queues with built in support for Kafka and [RSMQ](https://github.com/mlasevich/PyRSMQ) (Redis Simple Message Queue).

Use Volley if you need to quickly get up and running with a Python streaming application that consumes messages, processes them (and do other things), then publish results to some place.

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

4. Run the pre-built exampe:
`docker-compose up --build`

- `./example/external_data_producer.py` publishes sample data to `input-topic` Kafka topic.
- `./example/input_worker.py` consumes from `input-topic` and publishes to `comp_1` RSMQ queue. 
- `./example/comp1.py` consumes from `comp_1` RSMQ and publishes to `output-topic` Kafka topic.
- `./example/external_data_consumer.py` consumes from `output-topic` and logs to console.

## Getting started

Check out projects already using Volley:
  - [TLMD Future Route Actualizer](https://github.com/shipt/tlmd-future-route-actualizer) - Single worker that consumes from Kafka, does processing and invokes ML models, then publishes results to Kafka.
  - [Bundle Optimization Engine](https://github.com/shipt/ml-bundle-engine) - Collection of workers that consume/produce to Kafka, Redis, and Postgres. 


A full example is provided in `./example`. Run this example locally with `make run.example`.

Components are implemented as a function decorated with an instance of the `volley.engine.Engine`. A component consumes from one queue and can publish to one or many queues.

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
      return None
```

A component can also produce nothing.

```python
@engine.stream_app
def my_component_function(input_object: ComponentMessage) -> None:
    print(input_object.list_of_values)
    return None
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

# Engine

The engine itself is a python decorator that wraps a component worker and runs as headless services. The engine interacts with `Connectors`, `QueueMessages`, and the component function that it wraps.

On initialization:
- setup connections to the queues using the connectors specified by the components inputs and outputs
- determines the data schema required by the component

Once the engine has initialized, it will continuously poll the input queue for new messages. When it receives a message, it will process the message and pass it to the wrapped component function. It takes the output of the component function and produces it to the output queues. It will repeat this process until terminated.

## Connectors

Connectors are specific implementations of producers and consumers for a data store. There are currently connectors implemented for pyRSMQ and Kafka. 

Consumers and producers handle converting the `QueueMessage` objects to whichever data type and serialization is implemented in the specfic queue. For example, the pyRSMQ implementation stores messages as `JSON`, so the pyRSMQ producer converts the message in `QueueMessage` to JSON, then places the message on the queue. Likewise, pyRMSQ consumer read from JSON and convert to `QueueMessage`.

Components consume from one queue and produce to zero or many queues. Volley consumers and produces adhere to a consistent interface to conduct the following operations on any of the supported queues. These interfaces are designed in [Consumer and Producer](./volley/connectors/base.py) base classes.

Producers:

- `produce` - place a message on the queue.

- `shutdown` - gracefully disconnect the producer.

Consumers:

- `consume` - pull a message off the queue.

- `delete` - delete a message on the queue.

- `on_fail` - operation to conduct if a component worker fails processing a message. For example, place the message back on the queue, rollback a transaction, etc.

- `shutdown` - gracefully disconnect the consumer.

## Supported Connectors

Queues are the broker and backend that handle messages. Volley has connectors for two types of queue: 
- [pyRSMQ](https://github.com/mlasevich/PyRSMQ) is the python implementation of the [RSMQ](https://github.com/smrchy/rsmq) project. It is lightweight but full featured message queue system built on Redis. It provides clean interface to producing and consuming messages from a queue. It only supports strict FIFO - you cannot modify or update a message on the queue once it is produced. The number of messages that can exist in the queue is limited by the amount of memory available to Redis.

- Kafka - Volley's integration with Kafka is built on [confluent_kafka](https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html) and [pyshipt-streams](https://github.com/shipt/pyshipt-streams)

Supported connectors are specified in `volley_config.yml` by name.

```yml
- name: main_queue
  value: main_rsmq_queue
  type: rsmq
  schema: volley.data_models.ComponentMessage
```

# Extending Connectors with Plugins

Users can write their own connectors as needed. This is done by subclassing `volley.connects.base.Consumer|Producer`, then registering the connectors in `volley_config.yml`, along with the queue they are intended to connect to. The configuration below specifies an example connetor defined in `example.plugins.my_plugin` in the `MyPGProducer` and `MyPGConsumer` classes.

```yml
- name: postgres_queue
  value: pg_queue_table
  type: postgres
  schema: volley.data_models.ComponentMessage
  producer: example.plugins.my_plugin.MyPGProducer
  consumer: example.plugins.my_plugin.MyPGConsumer
```

# CI / CD

See `.drone.yml` for test gates. A Semantic tagged release triggers a build and publish to pypi.shipt.com.

# Testing

`make test.unit` Runs unit tests on individual components with mocked responses dependencies external to the code. Docker is not involved in this process.

`make test.integration` Runs an "end-to-end" test against the example project in `./example`. The tests validate messages make it through all supported connectors and queus, plus a user defined connector plugin (postgres).

# Metrics

Volley exports selected [Prometheus metrics](https://prometheus.io/docs/concepts/metric_types/) on all workers.

All metrics contain the label `volley_app` which is directly tied to the `app_name` parameter passed in when initializing `volley.engine.Engine()`.

### `messages_consumed_count` - [Counter](https://prometheus.io/docs/concepts/metric_types/#counter) 
- increments each time a message is consumed by the worker.
- Labels:
  - `status` : `success|fail`. If the worker consumes a message, but fails the corresponding produce operation, the message gets marked as a `fail`. Otherwise, it is a `success`.


### `messages_produced_count` - [Counter](https://prometheus.io/docs/concepts/metric_types/#counter)
- increments each time a message is produced
- Labels:
  - `source` : name of the queue the worker consumed from.
  - `destination` : name of the queue the message was produced to


### `process_time_seconds` - [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)
- observed the amount of time various processes take to run
- Labels:
  - `process_name` : name of the process that is tracked
    - Values:
      - `component` : time associated with the processing time for the function that Volley wraps. This is isolated to the logic in the user's function.
      - `cycle` : one full cycle of consume message, serialize, schema validation, component processing, and publishing to all outputs. `component` is a subset of `cycle`

### `redis_process_time_seconds` - [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)
- similar to `process_time_seconds` but is isolated to the RSMQ connector.
- Labels:
  - `operation`: name of the operation
    - `read` : time to read a message from the queue
    - `delete` : time to delete a message from the queue
    - `write` : time to add a message to the queue
    - `delete` : time to delete a message from the queue


Applications can export their own metrics as well. Examples in the Prometheus official [python client](https://github.com/prometheus/client_python) are a greaet place to start. The Volley exporter will collect these metrics are export expose them to be scraped by a Prometheus server.

# Support

`#ask-machine-learning`
