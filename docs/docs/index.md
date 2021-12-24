# **Volley**

Volley is a lightweight and highly configurable message stream processor for Python.



</a>


</a>

**Repository**: [https://github.com/shipt/volley](https://github.com/shipt/volley)

Use Volley to quickly build applications that need to poll streaming sources like Kafka, then process the data that it receives and publish results to one or many other streaming destinations.


## Pseudo Example

Volley turns your Python function into a stream processor. If you can write a Python function you can build stream a stream processor with Volley.

```python
from volley import Engine


app = Engine(
    input_queue="my_input_kafka_topic",
    output_queues=["my_output_kakfa_topic"],
)

@app.stream_app
def my_fun(msg: Any):
    print(msg)
    return [("my_output_kakfa_topic", msg)]

if __name__ == "__main__":
    my_fun()
```

And if your application needs to support `async` + `await`, define the function with `async def`:

```python
@app.stream_app
async def my_fun(msg: Any):
    out_msg = await some_awaitable(msg)
    return [("my_output_kakfa_topic", out_msg)]

if __name__ == "__main__":
    my_fun()
```

And start the worker:

```bash
python -m my_module.my_fun
```



See our [example](./example.md) for setting up a basic application.

## Features

Volley is production-ready, and provides the following to all functions that it wraps:

- Prometheus [Metrics](./metrics.md) for system observability
- Data validation via [Pydantic](https://pydantic-docs.helpmanual.io/)
- Built-in support for both Kafka and [pyRSMQ](https://github.com/mlasevich/PyRSMQ)(Redis)
- Serialization in JSON and [MessagePack](https://msgpack.org/index.html)
- Data validation and schemas, data store connectors, and serialization are all extensible with plugins
- Optional [dead-letter-queues](deadletterqueue.md) for serialization and schema validation failures

## Operations

When run, Volley invokes a continuous loop of the following:

  - poll the specified `input_queue` for new messages via a `connector`

  - the `connector` passes message through `serialization`

  - `serialization` passes the message through a `schema` for validation

  - message is passed to your function, and your function messages returns zero to many messages back to Volley

  - message passes through schema validation specified for the `output_queue`

  - message is serialized for `output_queue`

  - `connector` publishes message to `output_queue`


Messages that fail either `serialization` or `validation` are routed to a [dead-letter-queue](./deadletterqueue.md), if specified.