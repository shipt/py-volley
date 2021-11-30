# **Volley**

Volley is a lightweight message stream processor for Python.



</a>


</a>

**Repository**: [https://github.com/shipt/volley](https://github.com/shipt/volley)

Use Volley to quickly build applications that need to poll streaming sources like Kafka, then process the data is receives, and publish results to one or many other streaming destinations.


## Pseudo Example

Volley turns your Python function into a stream processor. If you can write a Python function you can build stream a stream processor with Volley.

```python
from volley.engine import Engine

from pydantic import BaseModel

app = Engine(
    input_queue="my_input_kafka_topic",
    output_queues=["my_output_kakfa_topic"],
)

@app.stream_app
def my_fun(msg: BaseModel):
    print(msg)
    return [("my_output_kakfa_topic", msg)]

```

See our [example](./example.md) for setting up a basic application.


## Features

Volley is production-ready, and provides the following to all functions that it wraps:

- Prometheus [Metrics](./metrics.md) for system observability
- Data validation via [Pydantic](https://pydantic-docs.helpmanual.io/)
- Built-in support for both Kafka and [pyRSMQ](https://github.com/mlasevich/PyRSMQ)(Redis)
- Serialization in JSON and [MessagePack](https://msgpack.org/index.html)
- Optional [dead-letter-queues](deadletterqueue.md) for serialization and schema validation failures

## Operations

When run, Volley invokes a continuous loop of the following:

  - poll the specified `input_queue` for new messages via a `connector`

  - the `connector` passes message through `serialization`

  - `serialization` passes the message through a `schema` for validation

  - message is passed to your function, and your function messages returns zero to many messages back to Volley

  - message passes through schema validation for specified for the `output_queue`

  - message is serialized for `output_queue`

  - `connector` publishes message to `output_queue`


Messages that fail either `serialization` or `validation` are routed to a [dead-letter-queue](./deadletterqueue.md), if specified.