All supported producer connector configurations are accessible through an optional third positional in the return tuple from the Volley application. Return a dictionary of configurations and they will be passed in to the producer as key-word arguments.

## Initialization Configurations

Configurations passed into `Engine()` init will be used in both Producer and Consumer constructors.

```python hl_lines="5"
cfg = {
    "output-topic": {
        "profile": "confluent",
        "producer": "volley.connectors.kafka.KafkaProducer",
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
        "consumer": "volley.connectors.kafka.KafkaConsumer",
        "config": {"bootstrap.servers": "kafka:9092", "group.id": "myConsumerGroup"},
    }
}
```
is equivalent to...

```python hl_lines="2"
from confluent_kafka import Consumer
c = Consumer({"bootstrap.servers": "kafka:9092", "group.id": "myConsumerGroup"})
```

## Producer Runtime Configuration
You will likely find the need to pass configuration or parameters directly to a producer at runtime. Some common examples of these are assigning a partition key in the Kafka producer or a visibility delay in an RSMQ producer.

```python 
return [
    ("output-topic", message_object, {"producer": "configs"})
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