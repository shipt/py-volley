# Connectors


## Overview

Connectors are specific implementations of producers and consumers for a data store. There are currently connectors implemented for [pyRSMQ](https://github.com/mlasevich/PyRSMQ) (Redis) and Kafka.


Producers have two functions:

- `produce` - place a message on the queue.

- `shutdown` - gracefully disconnect the producer.

Consumers have four functions:

- `consume` - pull a message off the queue.

- `delete` - delete a message on the queue.

- `on_fail` - operation to conduct if a component worker fails processing a message. For example, place the message back on the queue, rollback a transaction, etc.

- `shutdown` - gracefully disconnect the consumer. For example. close a database connection or leave a Kafka consumer group.

## Supported Connectors

Queues are the broker and backend that handle messages. Volley has built in support for two types of queue technoloigies; RSMQ and Kafka.

### pyRSMQ

The python implementation of the [RSMQ](https://github.com/smrchy/rsmq) project. It is lightweight but full featured message queue system built on Redis. It provides clean interface to producing and consuming messages from a queue. It only supports strict FIFO - you cannot modify or update a message on the queue once it is produced. The number of messages that can exist in the queue is limited by the amount of memory available to Redis.

Environment variables:
```bash
REDIS_HOST=host_to_run_rsmq
```

### Kafka

Implemented on [confluent_kafka](https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html).

The following configurations can be provided via environment variables:

```bash
KAFKA_CONSUMER_GROUP=<kafka_consumer_group>
KAFKA_KEY=<kafka username>
KAFKA_SECRET=<kafka password>
KAFKA_BROKERS=<host:port of the brokers>
```

But all [librdkafka configurations](https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md) can be passed through to the connector.

```yml
- name: output_topic
  value: output.kafka.topic.name
  profile: confluent
  data_model: volley.data_models.GenericMessage
  config:
    bootstrap.servers: kafka_broker_host:9092
```

## Extending Connectors with Plugins

Users can write their own connectors as needed. This is done by subclassing the corresponding `Producer` and `Consumer`, then registering them as a plugin connector in the engine configuration.

The base class for consumers and producers are clearly defined:

```python hl_lines="10 34"
# volley/connectors/base.py
{!../../volley/connectors/base.py!}
```

Consumers receive a `QueueMessage` object, which has two attributes; `message_context` and the `message` itself. `message_context` is used for actions such as `delete` (delete the message with `message_context` from the queue), or `on_fail` (place the message back on the queue).

Producers are simple. They publish `bytes` to a queue.

### Build a plugin

First, let's build a Consumer and Producer for Postgres.


```python
# my_plugin.py
{!../../example/plugins/my_plugin.py!}
```

The consumer has the specific implementations for `consume`, `on_success`, `on_fail`, and `shutdown`. The producer implements `produce` and `shutdown`.


### Register the plugin

Like all configuration, they can be specified in either `yaml` or a `dict` passed directly to `volley.engine.Engine` (but not both).

```yml
# ./my_volly_config.yml
- name: postgres_queue
  value: pg_queue_table
  data_model: volley.data_models.GenericMessage
  model_hander: volley.models.PydanticModelHandler
  serializer: None
  producer: example.plugins.my_plugin.MyPGProducer
  consumer: example.plugins.my_plugin.MyPGConsumer
```

Is is equivalent to:

```python
config = {
    "postgres_queue": {
        "value": "pg_queue_table",
        "data_model": "volley.data_models.GenericMessage,
        "model_hander": "volley.models.PydanticModelHandler",
        "serializer": "disabled",
        "producer": "example.plugins.my_plugin.MyPGProducer",
        "consumer": "example.plugins.my_plugin.MyPGConsumer"
    }
}
```

A complete example using this plugin is provided [here](../advanced_example.md)
