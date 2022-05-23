## Initialization Configurations

Configurations passed into `Engine()` init will be used in both Producer and Consumer constructors.

```python hl_lines="5"
from volley.connectors.confluent import ConfluentKafkaProducer
cfg = {
    "output-topic": {
        "profile": "confluent",
        "value": "my.kafka.topic",
        "producer": ConfluentKafkaProducer,
        "config": {"bootstrap.servers": "kafka:9092"},
    }
}
```

The above code snip is roughly equivalent to:

```python hl_lines="2"
from confluent_kafka import Producer
p = Producer({"bootstrap.servers": "kafka:9092"})
```

Likewise, consumer configurations are passed to consumer initializers.

```python hl_lines="5"
cfg = {
    "output-topic": {
        "profile": "confluent",
        "value": "my.kafka.topic",
        "consumer": "volley.connectors.confluent.ConfluentKafkaConsumer",
        "config": {"bootstrap.servers": "kafka:9092", "group.id": "myConsumerGroup"},
    }
}
```
is equivalent to...

```python hl_lines="2"
from confluent_kafka import Consumer
c = Consumer({"bootstrap.servers": "kafka:9092", "group.id": "myConsumerGroup"})
```

## Consumer's Runtime Message Context

Applications have the option to receive the raw runtime message context from Volley. This is accomplished by adding a reserved parameter, `msg_ctx` to their function definition. This can be valuable if the application needs access a lower level connector detail such as the message's Kafka partition, headers, offset, etc.

In a Kafka consumer, `msg_ctx` is the raw `confluent_kafka.Message` object returned from Poll(). In RSMQ, it is simply the message id. More generally, the `msg_ctx` is the value of `volley.data_models.QueueMessage.message_context`. Take note that it is a reference to the `QueueMessage`, and mutating the object may cause undesired results.

Receiving the `msg_ctx` does not change any behavior of Volley. Volley will still handle serialization and data validation according to the provided queue configuration, and if either of these fails the message will still be routed to the DLQ (if configured) or crash the application (if DLQ not configured).

Example using `msg_ctx` in a Confluent Kafka consumer.

```python
from confluent_kafka import Message

@app.stream_app
def main(message, msg_ctx: Message):
    partition = msg_ctx.partition()
    offset = msg_ctx.offset()
   ...
```

## Producer Runtime Configuration
All producer connector runtime configurations and parameters are accessible through an optional third positional in the return tuple from the Volley application. Return a dictionary of configurations and they will be passed in to the producer as key-word arguments.

Some common examples of these are assigning a partition key to a specific message in a Kafka producer or a visibility delay in an RSMQ producer.

```python
# example passing partition key for a message to the Kafka producer
return [
    ("output-topic", message_object, {"key": "<partition_key>"})
]
```

### Kafka
The Kafka producer is an implementation of Confluent's Python Producer. Some commonly used configurations are:
- `key: str` - partition key for the given message
- `headers: dict` - headers for the kafka message

A complete set of available configurations can be found in [Confluent's Producer Docs](https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#producer) and [librdkafka](https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md)

The following environment variables can be set in lieu of passing them as configuration:

`KAFKA_BROKERS` - maps to `bootstrap.servers`
`KAFKA_KEY` - maps to `sasl.username`
`KAFKA_SECRET` - maps to `sasl.password`

### Redis
The Redis producer is an implementation of the pyRSMQ project's producer. Most commonly used configurations:
- `delay: float` - amount of time for message to remain "invisible" to other consumers.

The complete list of configurations can be found in pyRSMQ's [sendMessage docs](https://github.com/mlasevich/PyRSMQ#redissmq-controller-api-usage)

`REDIS_HOST` environment variables maps to the `host` parameter in RSMQ configuration.