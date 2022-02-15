![VolleyFull-Horizontal](https://user-images.githubusercontent.com/81711984/149005139-f0441dcf-c76e-4112-baf1-998d0a6abdbb.png)


Volley is a lightweight and highly configurable message stream processor for Python.



</a>


</a>

**Repository**: [https://github.com/shipt/volley](https://github.com/shipt/volley)


Use Volley to quickly build lightweight message queue processing microservices. Write your applications and add a few lines of code to integrate with technologies like Kafka. Volley has built in connectors for [Confluent Kafka](https://github.com/confluentinc/confluent-kafka-python) and [Redis Simple Message Queue](https://github.com/mlasevich/PyRSMQ). It also provides serialization implementations in [MessagePack](https://github.com/msgpack/msgpack-python) and [orjson](https://github.com/ijl/orjson), as well as data validation with [Pydantic](https://github.com/samuelcolvin/pydantic) and [Prometheus](https://github.com/prometheus/client_python) metrics.


## Example

To demonstrate, let's create an application with two worker nodes. One consumes from Kafka, finds the maximum value in a list then publishes it to Redis. The other consumes the message from Redis - if the max value is > 10, it logs to console otherwise it constructs a new list and publishes to the same Kafka topic.

For most simple cases, you can use a [profile](./profiles.md) to define how your application should consume from or produce to a topic, as well as define handlers for serialization and data validation.

### Setup Kafka and Redis

We'll use these for our queues.

```bash
docker run -d -p 6379:6379 redis:5.0.0
docker run -d -p 9092:9092 bashj79/kafka-kraft
```

### Publish some sample data

Let's put a single message on the Kafka topic. Our sample application will process it.

```python
{!../../example/intro/single_message.py!}
```

### Configure queues

Let's put the configurations in `./my_config.py`. These configurations our worker nodes how to consume and produce to each queue. The [profile](./profiles.md) provides presets for serialization and connectors and the Pydantic model handler. The `InputMessage` and `OutputMessage` will be used for validating the data we consume. The `confluent` profile uses `orjson` as the default serializer.


```python
{!../../example/intro/my_config.py!}
```

### First worker node

We'll put the first worker node in app_0.py This node will consume from Kafka and produce to Redis. Configure the Engine() to point to the `input_queue` and `output_queues` specified in our `queue_config` we defined earlier.

The worker node is a function and it will receive a single object, which will be the message serialized and constructed into the `data_model` we specified in our `queue_config`.

The worker node can publish to zero or many outputs. When electing to not rely on Volley to route your message to another queue, simply return a `bool`. True will commit offsets to Kafka (or delete the message from Redis), and False will leave the message alone. Volley will produce all the messages you return to it by returning `List[Tuple[<name_of_queue>, message_object]]`

```python
{!../../example/intro/app_0.py!}
```

Then run the first worker

```bash
python app_0.py
```

Note: Volley supports `asyncio`, just prefix your function with `async`:
```python
@app.stream_app
async def my_fun(msg: Any):
```
### Second worker node

The second worker node is much like the first, except it will read from Redis and conditionally produce back to Kafka, or just create a log. We'll add some logic to make that slightly more interesting.

```python
{!../../example/intro/app_1.py!}
```

Then run the second worker node.

```bash
python app_1.py
```


You should see the following in your two terminals

__./app_0.py__
```
Received {"my_values": [1.0, 2.0, 3.0]}
the_max=3.0
Received {"my_values": [3.0, 4.0, 5.0]}
the_max=5.0
Received {"my_values": [5.0, 6.0, 7.0]}
the_max=7.0
Received {"my_values": [7.0, 8.0, 9.0]}
the_max=9.0
Received {"my_values": [9.0, 10.0, 11.0]}
the_max=11.0
```

__./app_1.py__
```
The maximum: 3.0
The maximum: 5.0
The maximum: 7.0
The maximum: 9.0
The maximum: 11.0
That's it, we are done!
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


Messages that fail either `serialization` or `validation` are routed to a [dead-letter-queue](./deadletterqueue.md), if specified. Users can also route messages to a dead-letter-queue the same as any other output queue.