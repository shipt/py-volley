# Volley

Documentation: https://animated-guacamole-53e254cf.pages.github.io/

Volley's goal is to make building event stream applications easier and more accessible to the Python community. Use Volley if you need to quickly develop streaming application to consumes messages, processes them (and do other things), then publish results to one or many places. Dead letters queues are also easily configured.

Volley provides an extensible Python interface to queue-like technologies with built in support for [Apache Kafka](https://kafka.apache.org/) and [RSMQ](https://github.com/mlasevich/PyRSMQ) (Redis Simple Message Queue). Volley is easily extended to any queue technology through plugins, and we provide an example for building a plugin for a Postgres queue in our [examples](./example/plugins/my_plugin.py)





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

By default, component function takes in `input_object` of type: `GenericMessage`, which is a Pydantic model that accepts extra attributes. This model defines the schema of messages on the INPUT_QUEUE. The component function can process and modify that object to meet its needs.

Components output a list of tuples, where the tuple is defined as `(<name_of_queue>, GenericMessage)`.
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
from volley.data_models import GenericMessage

queue_config = {
    "input-topic": {
      "value": "stg.kafka.myapp.input",
      "profile": "confluent",
      "data_model": "example.data_models.InputMessage",  # for input validation
    },
    "output-topic": {
      "value": "stg.ds-marketplace.v1.my_kafka_topic_output",
      "profile": "confluent",
      "data_model": "example.data_models.OutputMessage",  # for output validation
    },
    "dead-letter-queue": {
      "value": "stg.kafka.myapp.dlq",
      "profile": "confluent"
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
  
  out = GenericMessage(hello=out_value)

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
      "profile": "confluent",
      "data_model": "example.data_models.InputMessage",
    },
```

# CI / CD

See `.drone.yml` for test gates. A Semantic tagged release triggers a build and publish to pypi.shipt.com.

# Testing

`make test.unit` Runs unit tests on individual components with mocked responses dependencies external to the code. Docker is not involved in this process.

`make test.integration` Runs an "end-to-end" test against the example project in `./example`. The tests validate messages make it through all supported connectors and queues, plus a user defined connector plugin (postgres).


# Support

`#ask-machine-learning`
