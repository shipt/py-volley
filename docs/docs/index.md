![VolleyFull-Horizontal](https://user-images.githubusercontent.com/81711984/149005139-f0441dcf-c76e-4112-baf1-998d0a6abdbb.png)


Volley is a lightweight and highly configurable message stream processor for Python.

<a href="https://drone.shipt.com/shipt/volley" target="_blank">
    <img src="https://drone.shipt.com/api/badges/shipt/volley/status.svg?ref=refs/heads/main" alt="Test">
</a>
<a href="https://codecov.io/gh/shipt/volley" target="_blank">
    <img src="https://codecov.io/gh/shipt/volley/branch/main/graph/badge.svg?token=axP0uxJwPX" alt="Test">
</a>

**Repository**: [https://github.com/shipt/volley](https://github.com/shipt/volley)


Use Volley to quickly build lightweight message processing microservices. Write your applications and add a few lines of code to integrate with technologies like Kafka. Volley has built in connectors for [Confluent Kafka](https://github.com/confluentinc/confluent-kafka-python) and [Redis Simple Message Queue](https://github.com/mlasevich/PyRSMQ). It also provides serialization implementations in [MessagePack](https://github.com/msgpack/msgpack-python) and [orjson](https://github.com/ijl/orjson), as well as data validation via [Pydantic](https://github.com/samuelcolvin/pydantic) and [Prometheus](https://github.com/prometheus/client_python) metrics.


## Example

To consume from one Kafka topic and produce to another...

Define configuration for two topics; "input-topic" and "output-topic".

For most simple cases, you can use a [profile](./profiles.md) to define how your application should consume from or produce to a topic, as well as define handlers for serialization and data validation.

```python
cfg = {
    "input-topic": {  # a friendly name/alias for a queue
        "value": "my.kafka.topic",  # literal name of the queue
        "profile": "confluent",
    },
    "output-topic": {
        "value": "some.other.kafka.topic",
        "profile": "confluent",
        "data_model": "volley.data_models.GenericMessage"
    }
}
```

Initialize the Volley engine. Specify which queues from the above configuration are for inputs (consuming), and which are outputs (producing). You can consume and produce to the same queue.

```python
from volley import Engine

app = Engine(
    input_queue="input-topic",
    output_queues=["output-topic"],
    queue_config=cfg
)
```

Apply the `stream_app` decorator to your function. The message received by your function is a single message consumed from the Kafka topic.

You return a list of tuples from your function. Each list element contains `Tuple[<name_of_queue>, message_object]` these are the messages and their destination (queue) that Volley will produce for you. 

```python
from volley.data_models import GenericMessage

@app.stream_app
def my_fun(msg: Any):
    new_msg = GenericMessage(
        hello="world"
    )
    return [("output-topic", new_msg)]

if __name__ == "__main__":
    my_fun()
```

And if your application needs to support `async` + `await`, define the function with `async def`:

```python
@app.stream_app
async def my_fun(msg: Any):
    new_msg = GenericMessage(
        hello="world"
    )
    return [("output-topic", new_msg)]


if __name__ == "__main__":
    my_fun()
```

Ensure some variables are set in your environment.

```bash
KAFKA_BROKERS=kafka:9092
KAFKA_CONSUMER_GROUP=my.consumer.group
```

And start the worker:

```bash
python -m my_module.my_fun
```

See our [example](./example.md) for a more in-depth example.

## Features

Volley is production-ready, and provides the following to all functions that it wraps:

- Prometheus [Metrics](./metrics.md) for system observability
- Data validation via [Pydantic](https://pydantic-docs.helpmanual.io/)
- Built-in support for both Kafka and [pyRSMQ](https://github.com/mlasevich/PyRSMQ)(Redis)
- Serialization in JSON and [MessagePack](https://msgpack.org/index.html)
- Extensible data validation and schemas, data store connectors, and serialization with plugins
- Optional [dead-letter-queues](deadletterqueue.md) for serialization and schema validation failures

## How-it-works

Volley handles operations that need to happen before and after the processing in your function:

  - poll the specified `input_queue` for new messages via a `connector`

  - the `connector` passes message through `serialization`

  - `serialization` passes the message through a user provided `data_model` for schema validation

  - message is passed to your function, and your function messages returns zero to many messages back to Volley

  - message passes through schema validation specified for the `output_queue`

  - message is serialized for `output_queue`

  - `connector` publishes message to `output_queue`


Messages that fail either `serialization` or `validation` are routed to a [dead-letter-queue](./deadletterqueue.md), if specified.