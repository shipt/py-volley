# Volley

Documentation: https://animated-guacamole-53e254cf.pages.github.io/

Volley makes building event stream applications easier and more accessible. Use Volley if you need to quickly develop an application to consume messages, processes them (and do other things), then publish results to one or many places. Dead letters queues are also easily configured. Volley was very much inspired by the [Flask](https://github.com/pallets/flask) and [FastAPI](https://github.com/tiangolo/fastapi) projects, and aims to make working with queue based and event driven system as accessible as REST APIs.

Volley provides an extensible Python interface to queue-like technologies with built in support for [Apache Kafka](https://kafka.apache.org/) and [RSMQ](https://github.com/mlasevich/PyRSMQ) (Redis Simple Message Queue). Volley is easily extended to any queue technology through plugins. We provide an example for building a plugin for a Postgres queue in our [examples](./example/plugins/my_plugin.py)





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
## Feautres
- Built in support for [Apache Kafka](https://kafka.apache.org/) and [RSMQ](https://github.com/mlasevich/PyRSMQ)
- Optionally configured integration with dead-letter-queues
- [Prometheus](https://prometheus.io/) metrics for all operations such as function processing time, and consumption and production count.
- Serialization in JSON and [MessagePack](https://msgpack.org/index.html)
- Data validation via [Pydantic](https://pydantic-docs.helpmanual.io/)
- Extendible connectors (consumer/producers), serializers, model handlers, and model handlers via plugins.

## Getting started

Volley handles the process of consuming/producing by providing developers with extendible interaces and handlers:
- connectors - consumer and producer interfaces which define how the application should read messages, write messages, and what actions to take when a message is succesfully or fails processing.
- serializers - handlers and interface which describe the behavior for reading an byte objects from connectors. For example, Json or MessagePack serializers.
- model_handler - handler and interface which works very closely with serializers. Typically used to turn serialized data into a structured Python data model. Pydantic is Volley's most supported data_model and can handler serialization itself.
- data_model - When your application receives data from a queue, what schema and object do you expect it in? The data_model is provided by the user. And the `model_handler` describes how to construct your `data_model`.

Below is a basic example:
1) consumes from `input-topic` (a kafka topic).
2) evaluates the message from the queue
3) publishes a message to `output-queue`
4) Provides a path to a Pydantic model that provides schema validation to both inputs and outputs.
5) Configures a dead-letter queue for any incoming messages that violate the specified schema.


```python
# my_models.py
from pydantic import BaseModel

class InputMessage(BaseModel):
  my_values: list[int]
```

```python
# app.py
from typing import List, Tuple

from volley.engine import Engine
from volley.data_models import GenericMessage

queue_config = {
    "input-topic": {
      "value": "stg.kafka.myapp.input",
      "profile": "confluent",
      "data_model": "my_models.InputMessage"
    },
    "output-queue": {
      "value": "stg.ds-marketplace.v1.my_kafka_topic_output",
      "profile": "rsmq",
    },
}

app = Engine(
  app_name="my_volley_app",
  input_queue="input-topic",
  output_queues=["output-queue"],
  dead_letter_queue="dead-letter-queue",
  queue_config=queue_config
)

@app.stream_app
def hello_world(msg: InputMessage) -> List[Tuple[str, GenericMessage]]:
  max_val = max(msg.my_values)
  if max_val > 0:
    out_value = "foo"
  else:
    out_value = "bar"
  
  out = GenericMessage(hello=out_value)

  return [("output-topic", out)]  # a list of one or many output targets and messages
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
      "data_model": "my_models.InputMessage",
    },
    ...
```

## Complete example

Clone this repo and run `make run.example` to see a complete example of:
- consuming a message from a Kafka topic
- producing to RSMQ
- consuming from RSMQ and publishing to Kafka. Using a custom plugin to publish a Postgres based queue.

# CI / CD

See `.drone.yml` for test gates. A Semantic tagged release triggers a build and publish to pypi.shipt.com.

# Testing

`make test.unit` Runs unit tests on individual components with mocked responses dependencies external to the code. Docker is not involved in this process.

`make test.integration` Runs an "end-to-end" test against the example project in `./example`. The tests validate messages make it through all supported connectors and queues, plus a user defined connector plugin (postgres).


# Support

`#ask-machine-learning`
